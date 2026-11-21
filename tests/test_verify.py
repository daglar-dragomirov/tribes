import dspy
import pytest
from dspy.adapters.types.tool import ToolCallResults, ToolCalls

from tribes import Verifier, VerifierGate, steps
from tribes.forms import react_text, tool_observations
from tribes.verify import cites, distinct_candidates, parse_verdict


def P(answer, reasoning=""):
    return dspy.Prediction(answer=answer, reasoning=reasoning)


def history(*calls):
    """A DSPy >= 3.5 ReAct history with one event per (tool, args, value, is_error)."""
    msgs = []
    for name, args, value, err in calls:
        tc = ToolCalls(tool_calls=[ToolCalls.ToolCall(id="c", name=name, args=args)])
        res = ToolCallResults(tool_call_results=[ToolCallResults.ToolCallResult(call_id="c", name=name, value=value,
                                                                                 is_error=err)])
        msgs.append({"next_thought": f"use {name}", "tool_calls": tc.model_copy(update={"tool_call_results": res})})
    return dspy.History(messages=msgs)


# ---------------------------------------------------------------------- reading ReAct runs
def test_steps_reads_the_dspy_35_history():
    r = dspy.Prediction(verdict="B", history=history(("run_python", {"code": "print(6*7)"}, "42", False),
                                                     ("run_python", {"code": "1/0"}, "ZeroDivisionError", True),
                                                     ("submit", {"verdict": "B"}, {"verdict": "B"}, False)))
    s = steps(r)
    assert [x["tool"] for x in s] == ["run_python", "run_python", "submit"]
    assert s[0]["observation"] == "42" and s[1]["error"] is True
    assert tool_observations(r) == ["42"]
    assert "call: run_python" in react_text(r) and "submit" not in react_text(r)


def test_steps_reads_the_old_trajectory():
    r = dspy.Prediction(trajectory={"thought_0": "t", "tool_name_0": "search", "tool_args_0": {"q": "x"},
                                    "observation_0": "found", "thought_1": "done", "tool_name_1": "finish",
                                    "tool_args_1": {}, "observation_1": "Completed."})
    assert tool_observations(r) == ["found"]


# ---------------------------------------------------------------------- verdicts and the evidence gate
@pytest.mark.parametrize("text,n,out", [
    ("KEEP", 3, "KEEP"), ("B", 3, "B"), ("(C) is right", 3, "C"), ("Candidate B", 2, "B"), ("D", 3, None),
    ("I choose candidate A", 2, "A"), ("", 2, None), ("keep the current one", 2, "KEEP"),
])
def test_parse_verdict(text, n, out):
    assert parse_verdict(text, n) == out


def test_cites_needs_shared_content():
    assert cites("the brute force printed 1729", ["1729\n"])
    assert cites("rows: Oslo pen", ["name\npen | Oslo"])
    assert not cites("I am confident", ["42"])
    assert not cites("", ["42"]) and not cites("42", [])


class FakeAgent:
    """Stands in for the ReAct agent: returns scripted verdicts and tool observations, records candidate orders."""

    def __init__(self, script):
        self.script, self.seen = list(script), []

    def __call__(self, **kw):
        self.seen.append(kw["candidates"])
        verdict_for, obs, evidence = self.script.pop(0)
        letter = verdict_for(kw["candidates"])
        calls = [("run_python", {"code": "..."}, obs, False)] if obs is not None else []
        return dspy.Prediction(verdict=letter, evidence=evidence, history=history(*calls))


def letter_of(answer):
    def f(candidates):
        for block in candidates.split("\n\n"):
            if f"output: {answer}" in block:
                return block[1]
        return "KEEP"
    return f


def make_verifier(script, votes=3):
    v = Verifier(["question"], "answer", votes=votes)
    v.agent = FakeAgent(script)
    return v


CANDS = {"assembled": P("10", "r1"), "rigid": P("12", "r2"), "liquid": P("14", "r3")}


def test_keep_ends_after_one_call():
    v = make_verifier([(lambda c: "KEEP", "x", "")])
    d = v({"question": "q"}, CANDS, "assembled")
    assert d.choice == "assembled" and not d.switched and len(v.agent.seen) == 1


def test_switch_needs_a_majority_with_evidence():
    v = make_verifier([(letter_of("12"), "12", "printed 12")] * 3)
    d = v({"question": "q"}, CANDS, "assembled")
    assert d.choice == "rigid" and d.switched and d.votes == ["rigid"] * 3
    # the current choice is always A; the alternatives are rotated between calls
    assert all(s.startswith("[A] output: 10") for s in v.agent.seen)
    assert v.agent.seen[0] != v.agent.seen[1]


def test_switch_without_a_tool_observation_is_keep():
    v = make_verifier([(letter_of("12"), None, "trust me")])
    d = v({"question": "q"}, CANDS, "assembled")
    assert d.choice == "assembled" and d.votes == ["KEEP"] and len(v.agent.seen) == 1


def test_split_votes_keep_the_current_choice():
    v = make_verifier([(letter_of("12"), "12", "got 12"), (letter_of("14"), "14", "got 14"),
                       (lambda c: "KEEP", "x", "")])
    d = v({"question": "q"}, CANDS, "assembled")
    assert d.choice == "assembled" and not d.switched


def test_two_of_three_switch():
    v = make_verifier([(letter_of("14"), "14", "got 14"), (lambda c: "KEEP", "x", ""), (letter_of("14"), "14", "14")])
    assert v({"question": "q"}, CANDS, "assembled").choice == "liquid"


def test_single_vote_verifier_and_bad_votes():
    v = make_verifier([(letter_of("12"), "12", "12")], votes=1)
    assert v({"question": "q"}, CANDS, "assembled").choice == "rigid"
    with pytest.raises(ValueError):
        Verifier(["q"], "a", votes=2)


def test_evidence_sheet_is_rendered():
    v = Verifier(["question"], "answer", evidence=lambda inputs, p: f"facts about {p.answer}")
    text = v.render({"question": "q"}, list(CANDS.items()))
    assert "facts: facts about 12" in text and "[C] output: 14" in text


def test_gate():
    g = VerifierGate()
    assert g.passes(0.02, 3, 1)
    assert not g.passes(0.02, 2, 1)       # net 1 < 2
    assert not g.passes(0.004, 5, 0)      # gain too small
    assert not g.passes(0.05, 3, 3)


def test_distinct_candidates_one_per_answer():
    keys = {"rigid": "1", "assembled": "2", "liquid": "1"}
    preds = {f: P(k) for f, k in keys.items()}
    c = distinct_candidates(preds, keys, ["rigid", "liquid", "assembled"], "assembled",
                            ("assembled", "rigid", "liquid"))
    assert list(c) == ["assembled", "rigid"]
