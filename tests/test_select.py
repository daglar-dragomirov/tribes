import dspy
import pytest

from tribes import Tribes, non_inferior, paired_stats, pick, text_key


def test_vote_majority_and_reviewer_default():
    assert pick({"rigid": "a", "liquid": "a", "assembled": "b"}) == "rigid"
    assert pick({"rigid": "a", "liquid": "b", "assembled": "a"}) == "assembled"
    assert pick({"rigid": "a", "liquid": "b", "assembled": "c"}) == "assembled"


def test_liveness_fallback():
    assert pick({"rigid": "a", "liquid": "b", "assembled": None}) == "rigid"
    assert pick({"rigid": None, "liquid": "b", "assembled": None}) == "liquid"


def test_checker_drops_failing_forms_unless_all_fail():
    keys = {"rigid": "a", "liquid": "b", "assembled": "c"}
    assert pick(keys, {"rigid": True, "liquid": False, "assembled": False}) == "rigid"
    assert pick(keys, {"rigid": False, "liquid": False, "assembled": False}) == "assembled"


def test_lite_ignores_vote():
    assert pick({"rigid": "a", "liquid": "a", "assembled": "b"}, use_vote=False) == "assembled"


def test_text_key_normalises():
    assert text_key("The  Answer: 42.") == text_key("answer 42")


def test_non_inferiority():
    assert non_inferior([(i, 0.0) for i in range(10)])[0]
    assert not non_inferior([(i, -1.0) for i in range(10)])[0]
    use, m, se = non_inferior([(0, -0.5), (1, 0.5), (2, 0.0)])
    assert use and m == pytest.approx(0.0) and se > 0
    m, se = paired_stats([("a", 1.0), ("a", 0.0), ("b", 0.0), ("b", 0.0)])
    assert m == pytest.approx(0.25)


class _Fixed:
    def __init__(self, answer):
        self.answer = answer

    def __call__(self, **kw):
        if self.answer is None:
            raise ValueError("no output")
        return dspy.Prediction(answer=self.answer)


def _pt(rigid, assembled, liquid, mode="full"):
    prog = dspy.Predict("question -> answer")
    return Tribes(prog, mode=mode, forms={"rigid": _Fixed(rigid), "assembled": _Fixed(assembled),
                                              "liquid": _Fixed(liquid)}, retries=0)


def test_forward_full_and_lite():
    assert _pt("x", "y", "x")(question="q").answer == "x"
    assert _pt("x", "y", "z")(question="q").answer == "y"
    assert _pt("x", None, "z")(question="q").answer == "x"
    assert _pt("x", "y", "x", mode="lite")(question="q").answer == "y"


def test_fit_switches_layer_off_when_worse():
    data = [dspy.Example(question=str(i), answer="x").with_inputs("question") for i in range(20)]
    metric = lambda ex, pred: float(pred.answer == ex.answer)
    pt = _pt("x", "y", "z").fit(data, metric, num_threads=2)
    assert pt.use_layer is False and pt.report["mean_gain"] == pytest.approx(-1.0)
    pt = _pt("y", "x", "z").fit(data, metric, num_threads=2)
    assert pt.use_layer is True and pt.report["tribes_score"] == 1.0


def test_named_switches():
    from tribes import do_no_harm, non_inferiority, task_switch
    deltas = [(i, d) for i, d in enumerate([0.0] * 80 + [-1.0] * 10 + [1.0] * 6)]
    use, m, se = do_no_harm(deltas)
    assert use is (m + se >= 0)
    assert non_inferiority(deltas, margin=0.0)[0] is False
    assert task_switch(deltas, "non_inferiority", margin=0.5)[0] is True
    with pytest.raises(ValueError):
        task_switch(deltas, "vibes")


def test_switch_power_matches_the_known_operating_point():
    from tribes import switch_power
    # n = 100 binary differences (sd ~ 0.45): a layer truly 5 pp worse passes the 1.0 switch about 46 % of the time
    assert switch_power(-0.05, 0.45, 100) == pytest.approx(0.456, abs=0.01)
    assert switch_power(-0.05, 0.45, 300) < 0.2
    assert switch_power(0.05, 0.45, 100) > 0.9
    # the real non-inferiority test protects against a 5 pp loss
    assert switch_power(-0.05, 0.45, 100, "non_inferiority") < 0.05
    assert switch_power(0.0, 0.0, 10) == 1.0
