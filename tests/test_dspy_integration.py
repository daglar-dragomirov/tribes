"""End-to-end through real DSPy modules (Predict, ReAct, adapters, tools) with a scripted DummyLM: no network."""
import dspy
import pytest
from dspy.utils import DummyLM

from tribes import Liquid, Tribes, Verifier


def call(tool, **args):
    return {"tool_calls": [{"name": tool, "args": args}]}


def react(*turns):
    """ReAct turns: each (thought, tool, args); the agent's run_python calls really execute."""
    return [{"next_thought": t, "tool_calls": call(tool, **args)} for t, tool, args in turns]


@pytest.fixture(autouse=True)
def _reset():
    yield
    dspy.configure(lm=None)


def test_liquid_runs_tools_and_submits():
    dspy.configure(lm=DummyLM(react(("compute", "run_python", {"code": "print(6*7)"}),
                                    ("done", "submit", {"answer": "42"}))))
    r = Liquid(["question"], "answer", "Solve the problem.")(question="6*7?")
    assert r.answer == "42"
    assert "call: run_python" in r.reasoning and "-> 42" in r.reasoning


def test_full_pipeline_with_real_forms():
    program = dspy.Predict("question -> answer")
    script = ([{"answer": "5"}]                                      # rigid: the program
              + [{"answer": "5"}]                                    # assembled: the program's draft ...
              + react(("check", "run_python", {"code": "print(2+2)"}), ("fix", "submit", {"answer": "4"}))
              + react(("solve", "run_python", {"code": "print(2+2)"}), ("done", "submit", {"answer": "4"})))
    dspy.configure(lm=DummyLM(script))
    pt = Tribes(program, parallel=False, retries=0)
    sel = pt.explain(question="What is 2+2?")
    assert sel.reason == "vote" and sel.form == "assembled" and sel.prediction.answer == "4"
    assert sel.predictions["rigid"].answer == "5" and sel.predictions["assembled"].draft == "5"
    cost = pt.cost_report()
    assert set(cost["forms"]) == {"rigid", "assembled", "liquid"} and cost["total"]["failures"] == 0


def test_verifier_with_a_real_check():
    one = react(("test both", "run_python", {"code": "print(sum(range(1, 11)))"}),
                ("B is right", "submit", {"verdict": "B", "evidence": "the code printed 55"}))
    dspy.configure(lm=DummyLM(one * 3))
    v = Verifier(["question"], "answer")
    cands = {"assembled": dspy.Prediction(answer="50"), "liquid": dspy.Prediction(answer="55")}
    d = v({"question": "sum 1..10"}, cands, "assembled")
    assert d.choice == "liquid" and d.switched and d.gated == [True, True, True]


def test_verifier_without_a_check_cannot_switch():
    dspy.configure(lm=DummyLM([{"next_thought": "I just know", "tool_calls": call("submit", verdict="B",
                                                                                     evidence="obvious")}]))
    v = Verifier(["question"], "answer")
    cands = {"assembled": dspy.Prediction(answer="50"), "liquid": dspy.Prediction(answer="55")}
    d = v({"question": "sum 1..10"}, cands, "assembled")
    assert d.choice == "assembled" and d.votes == ["KEEP"]


def test_usage_rolls_up_into_an_outer_tracker():
    from dspy.utils.usage_tracker import track_usage
    program = dspy.Predict("question -> answer")
    dspy.configure(lm=DummyLM([{"answer": "1"}] * 4))
    pt = Tribes(program, forms={"rigid": program, "assembled": program, "liquid": program}, retries=0,
                    parallel=False)
    with track_usage():
        assert pt(question="q").answer == "1"
    assert pt.cost_report()["forms"]["rigid"]["calls"] == 1


def test_forms_and_retries_are_separate_cache_entries():
    """The program's run, the reviewer's draft and every retry must not collapse into one cached response."""
    seen = []

    def form(name, fail=0):
        state = {"n": 0}

        def f(**kw):
            seen.append((name, dspy.settings.lm.kwargs.get("rollout_id")))
            state["n"] += 1
            if state["n"] <= fail:
                raise ValueError("unparseable")
            return dspy.Prediction(answer="1")
        return f

    dspy.configure(lm=DummyLM([{"answer": "1"}]))
    pt = Tribes(dspy.Predict("question -> answer"), retries=1, parallel=False,
                    forms={"rigid": form("rigid", fail=1), "assembled": form("assembled"), "liquid": form("liquid")})
    pt(question="q")
    ids = [r for _, r in seen]
    assert len(ids) == len(set(ids)) == 3  # rigid attempt 0, rigid attempt 1, assembled attempt 0
    assert dspy.settings.lm.kwargs.get("rollout_id") is None  # the user's LM is untouched
    seen.clear()
    Tribes(dspy.Predict("question -> answer"), independent=False, parallel=False,
               forms={"rigid": form("r"), "assembled": form("a"), "liquid": form("l")})(question="q")
    assert {r for _, r in seen} == {None}
