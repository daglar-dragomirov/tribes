import dspy
import pytest
from conftest import FakeForm, examples

from tribes import tasks
from tribes.tasks import is_refusal, vote_merge


def P(answer):
    return dspy.Prediction(answer=answer)


def test_vote_merge_orders_by_support_then_rank():
    lists = {"assembled": ["a", "b", "c"], "rigid": ["b", "d"], "liquid": ["e", "b", "a"]}
    assert vote_merge(lists) == ["b", "a", "e", "d", "c"]  # ties: best rank first, then form priority
    assert vote_merge(lists, cap=2) == ["b", "a"]
    assert vote_merge({"rigid": ["X", "x", "y"]}) == ["X", "y"]  # normalised duplicates count once


def test_doc_set_merges_within_the_programs_budget():
    combine = tasks.doc_set("answer", cap="program").combine
    preds = {"rigid": P("Paris\nBerlin\nRome"), "assembled": P("Berlin\nMadrid\nOslo"), "liquid": P("Lisbon\nBerlin")}
    out = combine(preds, {}).answer.split("\n")
    assert len(out) == 3 and out[0] == "Berlin"
    unc = tasks.doc_set("answer", cap=None).combine(preds, {}).answer.split("\n")
    assert set(unc) == {"Paris", "Berlin", "Rome", "Madrid", "Oslo", "Lisbon"}
    lst = tasks.doc_set("answer", cap="program").combine({"rigid": P(["a", "b"]), "liquid": P(["b", "c"])}, {})
    assert lst.answer == ["b", "a"]
    assert tasks.doc_set("answer").combine({"rigid": P("")}, {}) is None


def test_merge_in_the_pipeline_and_in_fit(make_pt):
    gold = {"q1": {"A", "B"}, "q2": {"C", "Y"}}
    rigid = FakeForm(lambda i: {"q1": "A\nX", "q2": "C\nY"}[i["question"]])
    asm = FakeForm(lambda i: {"q1": "X\nZ", "q2": "D\nC"}[i["question"]])
    liq = FakeForm(lambda i: {"q1": "B\nA", "q2": "Y\nW"}[i["question"]])
    pt = make_pt(rigid, asm, liq, task=tasks.doc_set("answer", cap=2))
    sel = pt.explain(question="q1")
    assert sel.form == "merged" and sel.reason == "merge" and liq.calls == 1  # every form runs: no lazy skip
    assert set(sel.prediction.answer.split("\n")) == {"A", "X"}

    def recall(ex, pred, trace=None):
        return float(gold[ex.question] <= set(str(pred.answer).split("\n")))
    ds = examples([("q1", ""), ("q2", "")])
    pt.fit(ds, recall)
    assert "merged" in pt.report["form_scores"] and pt.report["picks"]["merged"] == 2
    assert pt.report["form_scores"]["merged"] == 0.5  # q2: {C, Y} wins the vote; q1 loses B to the cap of 2


def test_refusal_checker_drops_abstentions(make_pt):
    assert is_refusal("The answer cannot be determined from the tools.")
    assert is_refusal("Unknown") and not is_refusal("Lake Ontario")
    pt = make_pt("cannot be determined", "unknown", "Lake Ontario", task=tasks.tool_qa())
    assert pt(question="q").answer == "Lake Ontario"
    everyone = make_pt("unknown", "unknown", "not available", task=tasks.tool_qa())
    assert everyone.explain(question="q").form in ("assembled", "rigid")  # all abstain: nothing is dropped


@pytest.mark.parametrize("name", ["doc_set", "tool_qa"])
def test_new_presets_registered(name):
    assert name in tasks.PRESETS


def test_default_cap_is_the_longest_set():
    combine = tasks.doc_set("answer").combine
    out = combine({"rigid": P("a"), "assembled": P("b\nc\nd"), "liquid": P("e")}, {}).answer.split("\n")
    assert len(out) == 3
