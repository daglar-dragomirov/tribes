"""TRIBES 1.2 agent settings: the agents' own LM (the program keeps the task LM) and one retry on an empty or abstained
output."""
import dspy

from tribes import Tribes
from tribes.forms import Assembled, Liquid, _run_agent


class FakeAgent:
    """Records the LM in effect at each call and returns the queued outputs."""

    def __init__(self, outputs):
        self.outputs, self.seen = list(outputs), []

    def __call__(self, **kw):
        self.seen.append(dspy.settings.lm)
        return dspy.Prediction(answer=self.outputs.pop(0))


def test_agent_runs_with_its_own_lm():
    agent_lm, task_lm = object(), object()
    a = FakeAgent(["42"])
    with dspy.context(lm=task_lm):
        r = _run_agent(a, agent_lm, False, "answer", question="q")
        assert dspy.settings.lm is task_lm  # restored after the agent call
    assert r.answer == "42" and a.seen == [agent_lm]


def test_retry_once_on_refusal_or_empty():
    a = FakeAgent(["The answer cannot be determined.", "17"])
    assert _run_agent(a, None, True, "answer", question="q").answer == "17"
    b = FakeAgent(["", "5"])
    assert _run_agent(b, None, True, "answer", question="q").answer == "5"
    c = FakeAgent(["12", "never used"])
    assert _run_agent(c, None, True, "answer", question="q").answer == "12" and len(c.seen) == 1
    d = FakeAgent(["unknown", "unknown"])
    assert _run_agent(d, None, False, "answer", question="q").answer == "unknown" and len(d.seen) == 1


def test_tribes_passes_agent_settings_to_both_agents():
    prog = dspy.Predict("question -> answer")
    lm = object()
    t = Tribes(prog, agent_lm=lm, agent_retry=True, max_iters=16)
    for name in ("liquid", "assembled"):
        f = t.forms[name]
        assert isinstance(f, (Liquid, Assembled))
        assert f.lm_override is lm and f.retry is True and f.agent.max_iters == 16
    assert t.forms["rigid"] is prog


def test_default_is_unchanged():
    t = Tribes(dspy.Predict("question -> answer"))
    assert t.forms["liquid"].lm_override is None and t.forms["liquid"].retry is False
