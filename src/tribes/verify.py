"""The verifier: an evidence-gated agent for contested items.

After the item rule, some inputs stay *contested*: at least two different answers survive the liveness and checker
filters and no two forms agree. That is where the remaining gap to the per-item oracle sits on verifiable tasks. The
verifier settles them by a check, not by an opinion:

1. It sees the task, the inputs and the distinct candidate answers (A = the item rule's choice), each with an excerpt of
   its reasoning and an optional deterministic evidence sheet (public-test results, a query's result set, ...).
2. It must design and RUN one discriminating check with a tool -- a computation, substituting a candidate back into the
   conditions, code on edge-case inputs, an auxiliary SQL query -- whose outcome differs between the candidates, and
   then answer KEEP or a candidate letter, quoting the observation.
3. Evidence gate (code, not the model): a switch counts only if the run made a successful tool call and the quoted
   evidence shares content with an observation; otherwise it is KEEP.
4. Votes: one call; KEEP ends the item. A proposed switch triggers ``votes - 1`` more calls with the candidates in a
   rotated order; the switch needs a strict majority on the same answer.

Whether the verifier is used at all is decided per task in ``Tribes.fit`` (see ``VerifierGate``), on labeled
selection data, never by the verifier itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Mapping, Sequence

import dspy

from .forms import FINAL_TOOLS, run_python, steps

VERIFY_TEMPLATE = (
    "Several candidate outputs for this task disagree. Candidate A is the current choice. Decide which candidate is "
    "correct by evidence, not by opinion. First design ONE check whose outcome differs between the candidates: a "
    "calculation, a brute force or simulation, substituting a candidate back into the conditions of the task, running "
    "code on edge-case inputs, an auxiliary query or tool call on exactly the point where the candidates disagree. Then "
    "RUN it with a tool. Answer with the letter of the candidate that the observation supports, or KEEP if the check "
    "does not clearly separate them. In `evidence`, quote the part of the tool observation your verdict rests on. A "
    "verdict without a tool observation is treated as KEEP. Never answer with a candidate that is not listed.")

LETTERS = "ABCDEFGH"
_TOKEN = re.compile(r"-?\d+(?:\.\d+)?|[A-Za-z_][\w.]{3,}")


@dataclass
class VerifierGate:
    """Per-task enabling rule, applied in ``fit`` on the items the verifier actually changed.

    The verifier is enabled only if its mean gain over the item rule exceeds ``min_gain``, it won more switches than it
    lost and ``won - lost >= min_net``. Defaults follow the frozen research protocol.
    """
    min_gain: float = 0.005
    min_net: int = 2

    def passes(self, gain: float, won: int, lost: int) -> bool:
        return gain > self.min_gain and won > lost and won - lost >= self.min_net


@dataclass
class Verdict:
    choice: str            # the chosen form after the votes
    switched: bool
    votes: list[str]       # per call: "KEEP" or the form name the call voted for
    gated: list[bool]      # per call: did the evidence gate accept a proposed switch?
    evidence: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {"choice": self.choice, "switched": self.switched, "votes": self.votes, "gated": self.gated,
                "evidence": [e[:300] for e in self.evidence]}


def cites(evidence: str, observations: Sequence[str]) -> bool:
    """True if the quoted evidence shares a number or a word of 4+ characters with a tool observation, or quotes 12+
    consecutive characters of one."""
    ev = str(evidence or "")
    if not ev.strip() or not observations:
        return False
    toks = set(_TOKEN.findall(ev))
    for obs in observations:
        if toks & set(_TOKEN.findall(obs)):
            return True
        o = " ".join(obs.split())
        e = " ".join(ev.split())
        if any(e[i:i + 12] in o for i in range(0, max(1, len(e) - 11), 6)):
            return True
    return False


def parse_verdict(text: Any, n: int) -> str | None:
    """'KEEP' or a candidate letter among the first ``n``; None if unreadable (treated as KEEP)."""
    t = str(text or "").strip().upper()
    if not t:
        return None
    if t.startswith("KEEP") or re.match(r"^\W*KEEP\b", t):
        return "KEEP"
    m = re.match(r"^\W*(?:CANDIDATE\s+)?([A-H])\b", t)
    if m and LETTERS.index(m.group(1)) < n:
        return m.group(1)
    m = re.search(r"\b(?:CANDIDATE|ANSWER|CHOOSE|CHOICE)\W+([A-H])\b", t)
    if m and LETTERS.index(m.group(1)) < n:
        return m.group(1)
    return "KEEP" if "KEEP" in t else None


class Verifier(dspy.Module):
    """A ReAct verifier over the distinct candidate answers of one input.

    ``tools`` are the task's tools (the same the agents get); ``run_python`` is always available. ``evidence`` is an
    optional ``evidence(inputs, prediction) -> str`` that renders deterministic facts about one candidate.
    """

    def __init__(self, input_fields: Sequence[str], output_field: str, instructions: str = "",
                 tools: Sequence[Callable] = (), max_iters: int = 6, votes: int = 3,
                 evidence: Callable[[Mapping[str, Any], Any], str] | None = None, reasoning_chars: int = 1500):
        super().__init__()
        if votes < 1 or votes % 2 == 0:
            raise ValueError("votes must be an odd number >= 1")
        self.input_fields, self.output_field = list(input_fields), output_field
        self.votes, self.evidence, self.reasoning_chars = votes, evidence, reasoning_chars
        fields: dict[str, Any] = {k: (str, dspy.InputField()) for k in self.input_fields}
        fields["candidates"] = (str, dspy.InputField(desc="the distinct candidate outputs, labeled A, B, ..."))
        fields["verdict"] = (str, dspy.OutputField(desc="KEEP, or the letter of the correct candidate"))
        fields["evidence"] = (str, dspy.OutputField(desc="the quoted tool observation the verdict rests on"))
        head = (instructions.strip() + "\n\n") if instructions else ""
        sig = dspy.make_signature(fields, head + VERIFY_TEMPLATE)
        self.agent = dspy.ReAct(sig, tools=list(tools) + [run_python], max_iters=max_iters)

    # ------------------------------------------------------------------ rendering
    def render(self, inputs: Mapping[str, Any], cands: Sequence[tuple[str, Any]]) -> str:
        blocks = []
        for letter, (_, pred) in zip(LETTERS, cands):
            answer = getattr(pred, self.output_field, None)
            b = f"[{letter}] output: {answer}"
            r = str(getattr(pred, "reasoning", "") or "").strip()
            if r:
                b += f"\n    reasoning (excerpt): {r[-self.reasoning_chars:]}"
            if self.evidence is not None:
                try:
                    ev = self.evidence(inputs, pred)
                except Exception as e:
                    ev = f"(evidence unavailable: {type(e).__name__})"
                if ev:
                    b += f"\n    facts: {ev}"
            blocks.append(b)
        return "\n\n".join(blocks)

    # ------------------------------------------------------------------ one call
    def once(self, inputs: Mapping[str, Any], cands: Sequence[tuple[str, Any]]) -> tuple[str, bool, str]:
        """One verifier call over ``cands`` (first = the current choice). Returns (vote, gated, evidence) where vote is
        'KEEP' or a form name; a vote for a non-first candidate without gated evidence becomes 'KEEP'."""
        r = self.agent(**{k: inputs[k] for k in self.input_fields}, candidates=self.render(inputs, cands))
        v = parse_verdict(getattr(r, "verdict", None), len(cands))
        evidence = str(getattr(r, "evidence", "") or "")
        if v in (None, "KEEP"):
            return "KEEP", False, evidence
        form = cands[LETTERS.index(v)][0]
        if form == cands[0][0]:
            return "KEEP", False, evidence
        obs = [str(s["observation"]) for s in steps(r)
               if s["tool"] and s["tool"] not in FINAL_TOOLS and not s["error"] and s["observation"] not in (None, "")]
        ok = cites(evidence, obs)
        return (form if ok else "KEEP"), ok, evidence

    # ------------------------------------------------------------------ the voting protocol
    def forward(self, inputs: Mapping[str, Any], candidates: Mapping[str, Any], current: str,
                run: Callable[[Callable[[], Any]], Any] | None = None) -> Verdict:
        """Decide among ``candidates`` ({form: prediction}, one per distinct answer, including ``current``).

        ``run`` wraps each call (TRIBES passes its accounting / retry wrapper); a failed call counts as KEEP.
        """
        others = [f for f in candidates if f != current]
        order = [(current, candidates[current])] + [(f, candidates[f]) for f in others]
        call = run or (lambda thunk: thunk())

        def vote(o):
            out = call(lambda: self.once(inputs, o))
            return out if out is not None else ("KEEP", False, "")

        first = vote(order)
        votes, gated, evs = [first[0]], [first[1]], [first[2]]
        if first[0] == "KEEP" or self.votes == 1:
            choice = first[0] if first[0] != "KEEP" else current
            return Verdict(choice, choice != current, votes, gated, evs)
        for k in range(1, self.votes):
            rest = order[1:]
            rot = k % len(rest)
            v = vote([order[0]] + rest[rot:] + rest[:rot])
            votes.append(v[0])
            gated.append(v[1])
            evs.append(v[2])
        tally: dict[str, int] = {}
        for v in votes:
            if v != "KEEP":
                tally[v] = tally.get(v, 0) + 1
        best = max(tally, key=tally.get) if tally else None
        choice = best if best is not None and tally[best] * 2 > len(votes) else current
        return Verdict(choice, choice != current, votes, gated, evs)


def distinct_candidates(preds: Mapping[str, Any], keys: Mapping[str, Hashable | None], alive: Sequence[str],
                        current: str, order: Sequence[str]) -> dict[str, Any]:
    """One representative prediction per distinct answer key among ``alive``; the current choice represents its own."""
    seen: dict[Hashable, str] = {}
    for f in [current] + [f for f in order if f != current]:
        if f in alive and keys.get(f) is not None and keys[f] not in seen:
            seen[keys[f]] = f
    return {f: preds[f] for f in seen.values()}
