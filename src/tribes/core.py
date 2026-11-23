"""TRIBES: an optimizer-agnostic, never-worse layer on top of an optimized DSPy program."""
from __future__ import annotations

import asyncio
import contextlib
import contextvars
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Hashable, Iterable, Mapping, Sequence

import dspy
from dspy.utils.usage_tracker import track_usage

from .callbacks import Callback, emit
from .context import item_context
from .forms import ASSEMBLED_TEMPLATE, LIQUID_TEMPLATE, Assembled, Liquid, label_examples, task_text
from .select import FALLBACK, FORMS, contested, explain_pick, survivors, task_switch, text_key
from .tasks import Task
from .usage import Ledger, Prices, timed
from .verify import Verifier, VerifierGate, distinct_candidates

log = logging.getLogger("tribes")

FIT_FORMAT = 2


def _fields(program: dspy.Module, input_fields: Sequence[str] | None,
            output_field: str | None) -> tuple[list[str], str]:
    """The program's input fields (of its first predictor) and its single output field (of its last one)."""
    if input_fields is not None and output_field is not None:
        return list(input_fields), output_field
    preds = [p for _, p in program.named_predictors()]
    if not preds:
        raise ValueError("the program has no predictors; pass input_fields and output_field")
    inputs = list(input_fields) if input_fields is not None else list(preds[0].signature.input_fields)
    if output_field is not None:
        return inputs, output_field
    outs = [k for k in preds[-1].signature.output_fields if k != "reasoning"]
    if len(outs) != 1:
        raise ValueError(f"cannot infer the output field from {outs}; pass output_field")
    return inputs, outs[0]


def _parallel(thunks: Mapping[str, Callable[[], Any]], workers: int) -> dict[str, Any]:
    """Run independent thunks concurrently, each in a copy of the caller's context (DSPy settings, current item)."""
    if workers <= 1 or len(thunks) <= 1:
        return {k: f() for k, f in thunks.items()}
    with ThreadPoolExecutor(min(workers, len(thunks))) as pool:
        futs = {k: pool.submit(contextvars.copy_context().run, f) for k, f in thunks.items()}
        return {k: f.result() for k, f in futs.items()}


@dataclass
class Selection:
    """What TRIBES did for one input."""
    form: str                                   # the form whose prediction is returned
    reason: str                                 # vote / reviewer / fallback / none / verifier / program-only
    predictions: dict[str, Any] = field(default_factory=dict)
    keys: dict[str, Hashable | None] = field(default_factory=dict)
    checks: dict[str, bool | None] | None = None
    rule_form: str | None = None                # the item rule's choice before the verifier
    contested: bool = False
    verifier: dict[str, Any] | None = None

    @property
    def prediction(self) -> Any:
        return self.predictions.get(self.form)


class Tribes(dspy.Module):
    """Wrap an optimized DSPy program in the three TRIBES forms and the 1.0 selection rule.

    Typical use::

        pt = Tribes(optimized_program, task=tribes.tasks.math())
        pt.fit(selection_examples, metric)      # labeled data the optimizer saw (train + val) is fine
        prediction = pt(question="...")

    mode="full" runs the program and the reviewer concurrently, and the agent only when the two disagree (then a vote);
    mode="lite" runs the reviewer only (its draft is the program's output) and returns the reviewer's answer.
    ``verifier=True`` adds the evidence-gated verifier on contested items; ``fit`` enables it per task only if it pays.
    ``fit`` decides once per task whether the layer is used at all (non-inferiority on the selection data, ``z``
    standard errors); if not, the wrapped object behaves exactly like the program.

    TRIBES 1.2 settings: ``agent_lm`` gives the layer's own agents (reviewer and agent) their own LM, typically the task
    model at a higher reasoning effort, while the program and the reviewer's draft keep the task LM; for tool tasks
    ``max_iters=16`` and ``agent_retry=True`` (one fresh run when an agent's output is empty or an abstention).
    """

    def __init__(self, program: dspy.Module, *, input_fields: Sequence[str] | None = None,
                 output_field: str | None = None, tools: Sequence[Callable] = (), mode: str = "full",
                 task: Task | None = None,
                 answer_key: Callable[[Any], Hashable | None] | None = None,
                 checker: Callable[[Mapping[str, Any], Any], bool | None] | None = None,
                 verifier: bool | Verifier | None = None, verifier_votes: int = 3, verifier_iters: int = 6,
                 verifier_gate: VerifierGate | None = None,
                 z: float | None = None, switch: str = "do_no_harm", margin: float = 0.02,
                 max_iters: int = 8, retries: int = 3, examples: Sequence[dspy.Example] | None = None,
                 forms: Mapping[str, Callable[..., Any]] | None = None, parallel: bool = True,
                 callbacks: Iterable[Callback] = (), prices: Prices | None = None, independent: bool = True,
                 combine: Callable[[Mapping[str, Any], Mapping[str, Any]], Any] | None = None,
                 agent_lm: Any = None, agent_retry: bool = False):
        super().__init__()
        if mode not in ("full", "lite"):
            raise ValueError("mode must be 'full' or 'lite'")
        input_fields, output_field = _fields(program, input_fields, output_field)
        task = task or Task()
        self.program, self.mode, self.z, self.retries, self.parallel = program, mode, z, retries, parallel
        task_switch([], switch)  # validates the name
        self.switch, self.margin = switch, margin
        self.input_fields, self.output_field = list(input_fields), output_field
        self.answer_key = answer_key or task.answer_key
        self.checker = checker or task.checker
        self.evidence = task.evidence
        self.combine = combine or task.combine  # set-valued outputs: merge the forms instead of choosing one
        all_tools = list(tools) + [t for t in task.tools if t not in tools]
        head = task_text(program, label_examples(examples, output_field) if examples else None)
        if forms is None:  # ReAct modules hold no state until called
            forms = {"rigid": program,
                     "assembled": Assembled(program, self.input_fields, output_field,
                                            head + "\n\n" + ASSEMBLED_TEMPLATE, all_tools, max_iters,
                                            lm=agent_lm, retry=agent_retry),
                     "liquid": Liquid(self.input_fields, output_field, head + "\n\n" + LIQUID_TEMPLATE, all_tools,
                                      max_iters, lm=agent_lm, retry=agent_retry)}
        self.forms = dict(forms)
        if verifier is True:
            verifier = Verifier(self.input_fields, output_field, head, all_tools, verifier_iters, verifier_votes,
                                self.evidence)
        self.verifier: Verifier | None = verifier or None
        self.verifier_gate = verifier_gate or VerifierGate()
        self.callbacks = list(callbacks)
        self.independent = independent
        self.ledger = Ledger(prices)
        self.use_layer: bool | None = None     # None until fit(); then the task decision
        self.use_verifier: bool | None = None  # None until fit() (then used if present); then the verifier decision
        self.report: dict[str, Any] = {}

    # ------------------------------------------------------------------ one form, one input
    def _call(self, name: str, inputs: Mapping[str, Any], thunk: Callable[[], Any]) -> Any:
        """Run one form / verifier call with retries, accounting and callbacks; None if every attempt failed."""
        emit(self.callbacks, "on_form_start", name, inputs)
        out, err = None, None
        with timed() as t, track_usage() as tracker:
            for attempt in range(self.retries + 1):
                try:
                    with self._rollout(name, attempt):
                        out, err = thunk(), None
                    break
                except Exception as e:  # an output that cannot be parsed counts as no output after the retries
                    err = e
                    log.debug("%s failed (attempt %d): %s", name, attempt + 1, e)
        if err is not None:
            log.warning("%s failed after %d attempts: %s", name, self.retries + 1, err)
        usage = self.ledger.add(name, t[0], tracker.get_total_tokens(), out is not None)
        emit(self.callbacks, "on_form_end", name, inputs, out, err, usage)
        return out

    def _rollout(self, name: str, attempt: int):
        """Give every form and every retry its own cache entry.

        DSPy caches LM responses by request. Without this, the program's own run and the reviewer's draft of the same
        input are one cached response (the vote then compares a form with itself), and a retry after an unparseable
        output returns the same unparseable output. A distinct ``rollout_id`` per (form, attempt) makes them separate
        requests; results stay cached and reproducible across runs. Disable with ``independent=False``.
        """
        lm = dspy.settings.lm
        if not self.independent or lm is None or not hasattr(lm, "copy"):
            return contextlib.nullcontext()
        try:
            return dspy.context(lm=lm.copy(rollout_id=f"tribes:{name}:{attempt}"))
        except Exception as e:  # an LM that cannot be copied keeps its own caching
            log.debug("cannot set rollout_id on %s: %s", type(lm).__name__, e)
            return contextlib.nullcontext()

    def _run(self, form: str, inputs: Mapping[str, Any]) -> Any:
        return self._call(form, inputs, lambda: self.forms[form](**inputs))

    def _answer(self, pred: Any) -> Any:
        return None if pred is None else getattr(pred, self.output_field, None)

    def _key(self, pred: Any) -> Hashable | None:
        a = self._answer(pred)
        if a in (None, ""):
            return None
        try:
            return self.answer_key(pred) if self.answer_key else (text_key(a) or None)
        except Exception as e:
            log.debug("answer_key failed: %s", e)
            return None

    def _check(self, inputs: Mapping[str, Any], pred: Any) -> bool | None:
        if self.checker is None or pred is None:
            return None
        try:
            return self.checker(inputs, pred)
        except Exception:
            return None

    def _forms(self, inputs: Mapping[str, Any], lazy: bool) -> dict[str, Any]:
        """Run the forms the mode needs for one input."""
        workers = 3 if self.parallel else 1
        if self.mode == "lite":  # the reviewer; its draft (= one program run) stands in for the program
            preds = {"assembled": self._run("assembled", inputs)}
            a = preds["assembled"]
            draft = getattr(a, "draft_prediction", None) if a is not None else None
            preds["rigid"] = draft if draft is not None else (
                self._run("rigid", inputs) if self._key(a) is None or not lazy or self._verifier_active() else None)
            return preds
        lazy = lazy and self.combine is None  # a merge needs every form
        names = ["rigid", "assembled"] + ([] if lazy else ["liquid"])
        preds = _parallel({f: (lambda f=f: self._run(f, inputs)) for f in names}, workers)
        if lazy:
            ka, kr = self._key(preds["assembled"]), self._key(preds["rigid"])
            if ka is None or kr is None or ka != kr:
                preds["liquid"] = self._run("liquid", inputs)
        return preds

    def _verifier_active(self) -> bool:
        return self.verifier is not None and self.use_verifier is not False

    def _select(self, inputs: Mapping[str, Any], preds: dict[str, Any], verify: bool) -> Selection:
        keys = {f: self._key(preds.get(f)) for f in FORMS}
        checks = {f: self._check(inputs, preds.get(f)) for f in FORMS} if self.checker else None
        form, reason = explain_pick(keys, checks, use_vote=self.mode == "full")
        sel = Selection(form, reason, preds, keys, checks, rule_form=form, contested=contested(keys, checks))
        if self.combine is not None and self.mode == "full":
            alive = {f: preds[f] for f in survivors(keys, checks)}
            merged = None
            if alive:
                try:
                    merged = self.combine(alive, inputs)
                except Exception as e:
                    log.warning("combine failed: %s", e)
            if merged is not None:
                preds["merged"] = merged
                sel.form = sel.rule_form = "merged"
                sel.reason = "merge"
            return sel
        if verify and self.verifier is not None and sel.contested:
            alive = survivors(keys, checks)
            cands = distinct_candidates(preds, keys, alive, form, FALLBACK)
            if len(cands) >= 2 and form in cands:
                verdict = self._call("verifier", inputs, lambda: self.verifier(inputs, cands, form))
                if verdict is not None:
                    sel.verifier = verdict.as_dict()
                    if verdict.switched:
                        sel.form, sel.reason = verdict.choice, "verifier"
        return sel

    # ------------------------------------------------------------------ inference
    def explain(self, **inputs) -> Selection:
        """Run TRIBES on one input and return the full :class:`Selection` (all form outputs, keys, checks)."""
        missing = [k for k in self.input_fields if k not in inputs]
        if missing:
            raise TypeError(f"missing input fields: {missing}")
        with item_context(inputs):
            self.ledger.count_item()
            if self.use_layer is False:
                p = self._run("rigid", inputs)
                sel = Selection("rigid", "program-only", {"rigid": p})
            else:
                preds = self._forms(inputs, lazy=True)
                sel = self._select(inputs, preds, verify=self._verifier_active())
        emit(self.callbacks, "on_select", inputs, sel)
        return sel

    def forward(self, **inputs):
        if self.use_layer is False:  # exactly the program, errors included
            with item_context(inputs):
                self.ledger.count_item()
                return self.forms["rigid"](**inputs)
        sel = self.explain(**inputs)
        out = sel.prediction
        if out is None:  # every form failed: fall back to the program's own behaviour (it may raise)
            return self.forms["rigid"](**inputs)
        return out

    async def aforward(self, **inputs):
        """Async entry point (``await pt.acall(**inputs)``): runs the thread-based pipeline off the event loop."""
        return await asyncio.to_thread(self.forward, **inputs)

    def run_batch(self, items: Sequence[Mapping[str, Any] | dspy.Example], num_threads: int = 8,
                  return_selections: bool = False) -> list[Any]:
        """Predictions (or :class:`Selection` objects) for many inputs, ``num_threads`` items at a time, in order."""
        def one(item):
            inputs = {k: item[k] for k in self.input_fields}
            if return_selections:
                return self.explain(**inputs)
            try:
                return self.forward(**inputs)
            except Exception as e:
                log.warning("item failed: %s", e)
                return None
        with ThreadPoolExecutor(max(1, num_threads)) as pool:
            return list(pool.map(lambda it: contextvars.copy_context().run(one, it), items))

    async def abatch(self, items: Sequence[Mapping[str, Any] | dspy.Example], concurrency: int = 8) -> list[Any]:
        """Async counterpart of :meth:`run_batch`."""
        sem = asyncio.Semaphore(max(1, concurrency))

        async def one(item):
            async with sem:
                try:
                    return await self.aforward(**{k: item[k] for k in self.input_fields})
                except Exception as e:
                    log.warning("item failed: %s", e)
                    return None
        return list(await asyncio.gather(*(one(it) for it in items)))

    # ------------------------------------------------------------------ the task decision
    def fit(self, selection_set: Sequence[dspy.Example], metric: Callable[..., Any], num_threads: int = 8,
            cluster: Callable[[dspy.Example], Hashable] | None = None) -> Tribes:
        """Run the forms on labeled selection data and decide once whether the layer (and the verifier) is used."""
        def score(ex, pred):
            if pred is None:
                return 0.0
            try:
                return float(metric(ex, pred))
            except Exception:
                return 0.0

        def one(i_ex):
            i, ex = i_ex
            inputs = {k: ex[k] for k in self.input_fields}
            with item_context(inputs):
                preds = self._forms(inputs, lazy=False)
                if preds.get("rigid") is None:
                    preds["rigid"] = self._run("rigid", inputs)
                sel = self._select(inputs, preds, verify=self.verifier is not None)
            s = {f: score(ex, preds.get(f)) for f in (*FORMS, "merged") if f in preds}
            return {"i": i, "cluster": cluster(ex) if cluster else i, "rule_form": sel.rule_form, "form": sel.form,
                    "contested": sel.contested, "verifier": sel.verifier, "scores": s,
                    "keys": {f: None if k is None else str(k) for f, k in sel.keys.items()},
                    "checks": sel.checks}

        prev = self.use_layer
        self.use_layer = None  # fit always measures the layer
        try:
            with ThreadPoolExecutor(max(1, num_threads)) as pool:
                rows = list(pool.map(lambda x: contextvars.copy_context().run(one, x), enumerate(selection_set)))
        except BaseException:
            self.use_layer = prev
            raise
        n = len(rows)

        # the verifier's own gate: only the items it changed matter
        vrep: dict[str, Any] | None = None
        if self.verifier is not None:
            won = sum(1 for r in rows if r["form"] != r["rule_form"]
                      and r["scores"][r["form"]] > r["scores"][r["rule_form"]])
            lost = sum(1 for r in rows if r["form"] != r["rule_form"]
                       and r["scores"][r["form"]] < r["scores"][r["rule_form"]])
            gain = (sum(r["scores"][r["form"]] - r["scores"][r["rule_form"]] for r in rows) / n) if n else 0.0
            self.use_verifier = self.verifier_gate.passes(gain, won, lost)
            vrep = {"enabled": self.use_verifier, "gain": gain, "won": won, "lost": lost,
                    "contested": sum(1 for r in rows if r["contested"]),
                    "switched": sum(1 for r in rows if r["form"] != r["rule_form"])}
        for r in rows:
            r["final_form"] = r["form"] if self.use_verifier else r["rule_form"]

        use, m, se = task_switch([(r["cluster"], r["scores"][r["final_form"]] - r["scores"]["rigid"]) for r in rows],
                                 self.switch, self.z, self.margin)
        self.use_layer = use
        self.report = {"format": FIT_FORMAT, "n": n, "use_layer": use, "mean_gain": m, "se": se, "z": self.z,
                       "switch": self.switch, "margin": self.margin if self.switch == "non_inferiority" else None,
                       "mode": self.mode,
                       "program_score": sum(r["scores"]["rigid"] for r in rows) / n if n else 0.0,
                       "tribes_score": sum(r["scores"][r["final_form"]] for r in rows) / n if n else 0.0,
                       "oracle_score": sum(max(r["scores"].values()) for r in rows) / n if n else 0.0,
                       "form_scores": {f: sum(r["scores"].get(f, 0.0) for r in rows) / n if n else 0.0
                                       for f in (*FORMS, *(("merged",) if self.combine else ()))},
                       "picks": {f: sum(1 for r in rows if r["final_form"] == f)
                                 for f in (*FORMS, *(("merged",) if self.combine else ()))},
                       "verifier": vrep, "cost": self.ledger.summary(), "items": rows}
        log.info("fit: use_layer=%s gain=%+.4f se=%.4f n=%d%s", use, m, se, n,
                 "" if vrep is None else f" verifier={'on' if vrep['enabled'] else 'off'} "
                                         f"(+{vrep['won']}/-{vrep['lost']})")
        emit(self.callbacks, "on_fit_end", self.report)
        return self

    # ------------------------------------------------------------------ persistence and accounting
    def decision(self) -> dict[str, Any]:
        """The fitted task decision without per-item rows (small, JSON-serialisable)."""
        return {k: v for k, v in self.report.items() if k != "items"} | {
            "format": FIT_FORMAT, "use_layer": self.use_layer, "use_verifier": self.use_verifier, "mode": self.mode,
            "z": self.z, "output_field": self.output_field, "input_fields": self.input_fields}

    def save_fit(self, path: str, items: bool = False) -> None:
        """Save the task decision (and optionally the per-item rows, which ``tribes replay`` reads)."""
        data = self.decision()
        if items:
            data["items"] = self.report.get("items", [])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_fit(self, path: str) -> Tribes:
        """Restore a saved task decision, so a deployed program does not re-run ``fit``."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("mode") not in (None, self.mode):
            raise ValueError(f"the decision was fitted in mode {data.get('mode')!r}, this object is {self.mode!r}")
        if data.get("output_field") not in (None, self.output_field):
            raise ValueError("the decision was fitted for a different output field")
        self.use_layer = data.get("use_layer")
        self.use_verifier = data.get("use_verifier")
        self.report = data
        return self

    def cost_report(self) -> dict[str, Any]:
        """Calls, failures, seconds, tokens and dollars per form since construction (or ``ledger.reset()``)."""
        return self.ledger.summary()
