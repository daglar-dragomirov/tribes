import asyncio
import io
import json
import threading

import dspy
import pytest
from conftest import FakeForm, exact, examples

from tribes import Callback, JSONLCallback, Tribes, Verdict, current_inputs, tasks


# ---------------------------------------------------------------------- inference: full mode
def test_full_mode_agreement_skips_the_agent(make_pt):
    liquid = FakeForm("x")
    pt = make_pt("42", "42", liquid)
    assert pt(question="q").answer == "42"
    assert liquid.calls == 0


def test_full_mode_disagreement_runs_the_agent_and_votes(make_pt):
    liquid = FakeForm("41")
    pt = make_pt("41", "42", liquid)
    sel = pt.explain(question="q")
    assert liquid.calls == 1
    assert sel.form == "rigid" and sel.reason == "vote" and sel.prediction.answer == "41"


def test_full_mode_three_way_split_keeps_the_reviewer(make_pt):
    sel = make_pt("1", "2", "3").explain(question="q")
    assert sel.form == "assembled" and sel.reason == "reviewer" and sel.contested


def test_program_and_reviewer_run_concurrently(make_pt):
    barrier = threading.Barrier(2)  # deadlocks (BrokenBarrierError after 5 s) unless both run at once
    pt = make_pt(FakeForm("7", barrier=barrier), FakeForm("7", barrier=barrier), "7")
    assert pt(question="q").answer == "7"


def test_sequential_mode_never_overlaps(make_pt):
    active, peak, lock = [0], [0], threading.Lock()

    def ans(_):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        import time
        time.sleep(0.02)
        with lock:
            active[0] -= 1
        return "1"
    pt = make_pt(FakeForm(ans), FakeForm(ans), FakeForm(ans), parallel=False)
    pt(question="q")
    assert peak[0] == 1


def test_answer_key_merges_equivalent_answers(make_pt):
    liquid = FakeForm("x")
    pt = make_pt("\\boxed{1/2}", "0.5", liquid, task=tasks.math())
    assert pt.explain(question="q").reason == "vote"
    assert liquid.calls == 0


def test_checker_drops_failing_forms(make_pt):
    pt = make_pt("bad", "worse", "good", checker=lambda inputs, p: p.answer == "good")
    assert pt.explain(question="q").form == "liquid"


def test_failed_form_counts_as_no_output_and_retries(make_pt):
    rigid = FakeForm("5", fail_times=1)
    pt = make_pt(rigid, FakeForm(ValueError("x")), "5", retries=1)
    sel = pt.explain(question="q")
    assert rigid.calls == 2
    assert sel.predictions["assembled"] is None and sel.prediction.answer == "5"


def test_every_form_failing_falls_back_to_the_program(program, make_pt):
    rigid = FakeForm("program", fail_times=1)  # fails inside the layer, answers when called as the fallback
    pt = make_pt(rigid, ValueError("b"), ValueError("c"))
    assert pt(question="q").answer == "program" and rigid.calls == 2
    with pytest.raises(ValueError):
        make_pt(ValueError("a"), ValueError("b"), ValueError("c"))(question="q")  # the program's own error


def test_missing_input_field_is_an_error(make_pt):
    with pytest.raises(TypeError):
        make_pt("1", "1", "1").explain(other="q")


def test_forms_see_the_current_item(make_pt):
    seen = []
    pt = make_pt(FakeForm(lambda i: seen.append(current_inputs()["question"]) or "a"), "a", "a")
    pt(question="hello")
    assert seen == ["hello"]
    with pytest.raises(RuntimeError):
        current_inputs()


# ---------------------------------------------------------------------- inference: lite mode
def test_lite_returns_the_reviewer_and_uses_its_draft(make_pt):
    rigid = FakeForm("draft")
    draft = dspy.Prediction(answer="draft")
    pt = make_pt(rigid, FakeForm("reviewed", extra={"draft_prediction": draft}), "x", mode="lite")
    sel = pt.explain(question="q")
    assert sel.form == "assembled" and sel.predictions["rigid"] is draft and rigid.calls == 0


def test_lite_falls_back_to_the_draft(make_pt):
    draft = dspy.Prediction(answer="draft")
    pt = make_pt("x", FakeForm("", extra={"draft_prediction": draft}), "x", mode="lite")
    assert pt(question="q").answer == "draft"


def test_lite_runs_the_program_when_the_reviewer_crashes(make_pt):
    rigid = FakeForm("prog")
    pt = make_pt(rigid, FakeForm(ValueError("boom")), "x", mode="lite")
    assert pt(question="q").answer == "prog" and rigid.calls == 1


def test_bad_mode():
    with pytest.raises(ValueError):
        Tribes(dspy.Predict("question -> answer"), mode="turbo")


# ---------------------------------------------------------------------- the task decision
def _ds(n=12):
    return examples([(f"q{i}", f"a{i}") for i in range(n)])


def test_fit_uses_the_layer_when_it_helps(make_pt):
    good = lambda i: "a" + i["question"][1:]  # noqa: E731
    pt = make_pt("wrong", good, good).fit(_ds(), exact, num_threads=4)
    assert pt.use_layer is True
    r = pt.report
    assert r["program_score"] == 0.0 and r["tribes_score"] == 1.0 and r["mean_gain"] == 1.0
    assert r["oracle_score"] == 1.0 and r["picks"]["assembled"] == 12
    assert len(r["items"]) == 12


def test_fit_switches_the_layer_off_when_it_hurts(make_pt):
    good = lambda i: "a" + i["question"][1:]  # noqa: E731
    rigid = FakeForm(good)
    pt = make_pt(rigid, "wrong", "wrong").fit(_ds(), exact)
    assert pt.use_layer is False and pt.report["mean_gain"] == -1.0
    calls = rigid.calls
    out = pt(question="q3")
    assert out.answer == "a3" and rigid.calls == calls + 1
    assert pt.explain(question="q3").reason == "program-only"


def test_fit_runs_every_form_on_every_item(make_pt):
    liquid = FakeForm("same")
    make_pt("same", "same", liquid).fit(_ds(5), exact)
    assert liquid.calls == 5  # not lazy during fit: the scores of all forms are needed


def test_fit_clusters_repeated_items(make_pt):
    ds = examples([("q1", "a1")] * 4 + [("q2", "a2")] * 4)
    flip = lambda i: "a1" if i["question"] == "q1" else "x"  # noqa: E731
    pt = make_pt("x", flip, flip).fit(ds, exact, cluster=lambda ex: ex.question)
    assert pt.report["se"] > 0 and pt.report["mean_gain"] == 0.5


def test_fit_with_noisy_small_gain_is_non_inferior(make_pt):
    ds = _ds(20)
    win = {f"q{i}" for i in range(0, 20, 3)}
    rigid = lambda i: "a" + i["question"][1:] if i["question"] not in win else "x"  # noqa: E731
    lose = {"q1"}
    asm = lambda i: "a" + i["question"][1:] if i["question"] not in lose else "x"  # noqa: E731
    pt = make_pt(rigid, asm, "zzz").fit(ds, exact)
    assert pt.use_layer is True and pt.report["mean_gain"] > 0


# ---------------------------------------------------------------------- the verifier
class FakeVerifier:
    """Switches to the candidate whose answer is ``truth(inputs)``."""

    def __init__(self, truth):
        self.truth, self.calls = truth, 0

    def __call__(self, inputs, candidates, current):
        self.calls += 1
        t = self.truth(inputs)
        for f, p in candidates.items():
            if p.answer == t and f != current:
                return Verdict(f, True, [f], [True], ["obs"])
        return Verdict(current, False, ["KEEP"], [False], [""])


def test_verifier_runs_only_on_contested_items(make_pt):
    v = FakeVerifier(lambda i: "3")
    pt = make_pt("1", "1", "3", verifier=v)
    assert pt(question="q").answer == "1" and v.calls == 0
    pt2 = make_pt("1", "2", "3", verifier=v)
    sel = pt2.explain(question="q")
    assert v.calls == 1 and sel.form == "liquid" and sel.reason == "verifier" and sel.rule_form == "assembled"


def test_fit_enables_a_verifier_that_wins(make_pt):
    truth = lambda i: "a" + i["question"][1:]  # noqa: E731
    v = FakeVerifier(truth)
    pt = make_pt("r", "s", truth, verifier=v).fit(_ds(), exact)
    rep = pt.report["verifier"]
    assert pt.use_verifier is True and rep["won"] == 12 and rep["lost"] == 0
    assert pt.use_layer is True and pt.report["tribes_score"] == 1.0


def test_fit_disables_a_verifier_that_loses(make_pt):
    truth = lambda i: "a" + i["question"][1:]  # noqa: E731
    v = FakeVerifier(lambda i: "r")           # always switches to the wrong program answer
    pt = make_pt("r", truth, "z", verifier=v).fit(_ds(), exact)
    assert pt.use_verifier is False and pt.report["verifier"]["lost"] == 12
    calls = v.calls
    assert pt(question="q2").answer == "a2" and v.calls == calls  # off: not even called


def test_lite_verifier_compares_reviewer_and_draft(make_pt):
    draft = dspy.Prediction(answer="right")
    v = FakeVerifier(lambda i: "right")
    pt = make_pt("x", FakeForm("wrong", extra={"draft_prediction": draft}), "x", mode="lite", verifier=v)
    sel = pt.explain(question="q")
    assert sel.form == "rigid" and sel.prediction.answer == "right"


def test_a_crashing_verifier_keeps_the_rule(make_pt):
    def boom(*a, **k):
        raise RuntimeError("verifier down")
    sel = make_pt("1", "2", "3", verifier=boom).explain(question="q")
    assert sel.form == "assembled" and sel.verifier is None


# ---------------------------------------------------------------------- batch, async, callbacks, cost, persistence
def test_run_batch_keeps_order(make_pt):
    pt = make_pt(lambda i: i["question"].upper(), lambda i: i["question"].upper(), "z")
    items = [{"question": f"q{i}"} for i in range(20)]
    assert [p.answer for p in pt.run_batch(items, num_threads=6)] == [f"Q{i}" for i in range(20)]
    sels = pt.run_batch(examples([("a", "b")]), return_selections=True)
    assert sels[0].form == "assembled"


def test_async_call_and_batch(make_pt):
    pt = make_pt("1", "1", "z")
    assert asyncio.run(pt.acall(question="q")).answer == "1"
    outs = asyncio.run(pt.abatch([{"question": str(i)} for i in range(5)], concurrency=2))
    assert [o.answer for o in outs] == ["1"] * 5


def test_callbacks_see_every_event_and_cannot_break_the_run(make_pt):
    events = []

    class Rec(Callback):
        def on_form_start(self, form, inputs):
            events.append(("start", form))

        def on_form_end(self, form, inputs, prediction, error, usage):
            events.append(("end", form, prediction is not None))

        def on_select(self, inputs, selection):
            events.append(("select", selection.form))

        def on_fit_end(self, report):
            events.append(("fit", report["use_layer"]))

    class Broken(Callback):
        def on_select(self, inputs, selection):
            raise RuntimeError("observability bug")

    stream = io.StringIO()
    pt = make_pt("1", "2", "1", callbacks=[Rec(), Broken(), JSONLCallback(stream)])
    assert pt(question="q").answer == "1"
    assert ("select", "rigid") in events and sum(1 for e in events if e[0] == "end") == 3
    pt.fit(examples([("q", "1")]), exact)
    assert events[-1] == ("fit", True)
    rows = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert {r["event"] for r in rows} == {"form", "select", "fit"}


def test_cost_report_counts_calls_and_failures(make_pt):
    pt = make_pt("1", FakeForm(ValueError("x")), "1")
    pt(question="q")
    c = pt.cost_report()
    assert c["items"] == 1
    assert c["forms"]["assembled"]["failures"] == 1 and c["forms"]["rigid"]["calls"] == 1
    assert c["total"]["calls"] == 3


def test_save_and_load_the_decision(tmp_path, make_pt):
    pt = make_pt("wrong", lambda i: "a" + i["question"][1:], "z").fit(_ds(6), exact)
    path = tmp_path / "fit.json"
    pt.save_fit(str(path), items=True)
    data = json.loads(path.read_text())
    assert data["use_layer"] is True and len(data["items"]) == 6
    fresh = make_pt("wrong", "x", "z")
    assert fresh.load_fit(str(path)).use_layer is True
    lite = make_pt("1", "1", "1", mode="lite")
    with pytest.raises(ValueError):
        lite.load_fit(str(path))


def test_task_tools_reach_the_default_agents(program):
    def my_tool(x: str) -> str:
        """A task tool."""
        return x
    pt = Tribes(program, tools=[my_tool], task=tasks.math())
    for form in ("assembled", "liquid"):
        names = set(pt.forms[form].agent.tools)
        assert {"my_tool", "run_python"} <= names
    assert pt.answer_key is not None
    pt_v = Tribes(program, verifier=True, task=tasks.choice())
    assert "run_python" in pt_v.verifier.agent.tools


def test_infers_fields_and_rejects_ambiguous_programs():
    pt = Tribes(dspy.ChainOfThought("context, question -> answer"))
    assert pt.input_fields == ["context", "question"] and pt.output_field == "answer"
    with pytest.raises(ValueError):
        Tribes(dspy.Predict("question -> answer, confidence"))
    pt2 = Tribes(dspy.Predict("question -> answer, confidence"), output_field="answer")
    assert pt2.output_field == "answer"


def test_fit_with_the_non_inferiority_switch(make_pt):
    ds = _ds(10)
    same = lambda i: "a" + i["question"][1:]  # noqa: E731
    pt = make_pt(same, same, same, switch="non_inferiority", margin=0.0).fit(ds, exact)
    assert pt.report["switch"] == "non_inferiority" and pt.use_layer is True  # exactly equal: m = se = 0
    with pytest.raises(ValueError):
        make_pt("1", "1", "1", switch="magic")
