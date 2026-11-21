import json

import pytest

from tribes import Ledger, replay
from tribes.cli import main
from tribes.replay import bootstrap_ci, load_rows
from tribes.usage import price

ROWS = [
    # agreement of program and reviewer, both right
    {"cluster": 1, "keys": {"rigid": "a", "assembled": "a", "liquid": None}, "scores": {"rigid": 1, "assembled": 1}},
    # reviewer fixes the program; the agent agrees with the reviewer
    {"cluster": 2, "keys": {"rigid": "x", "assembled": "b", "liquid": "b"},
     "scores": {"rigid": 0, "assembled": 1, "liquid": 1}},
    # contested; the verifier picks the right agent answer
    {"cluster": 3, "keys": {"rigid": "x", "assembled": "y", "liquid": "c"},
     "scores": {"rigid": 0, "assembled": 0, "liquid": 1}, "verifier": "liquid"},
    # program and agent agree on a wrong answer against a right reviewer (vote loses)
    {"cluster": 4, "keys": {"rigid": "w", "assembled": "d", "liquid": "w"},
     "scores": {"rigid": 0, "assembled": 1, "liquid": 0}},
]


def test_replay_full_with_and_without_verifier():
    r = replay(ROWS, "full")
    assert r["n"] == 4 and r["program"] == 0.25 and r["oracle"] == 1.0
    assert r["tribes"] == 0.75 and r["picks"]["liquid"] == 1 and r["contested"] == 1
    assert replay(ROWS, "full", use_verifier=False)["tribes"] == 0.5
    lite = replay(ROWS, "lite", use_verifier=False)
    assert lite["tribes"] == 0.75  # the reviewer alone; no vote to lose row 4
    assert replay([])["n"] == 0


def test_replay_decision_and_checks():
    rows = [{"keys": {"rigid": "a", "assembled": "b", "liquid": "c"}, "scores": {"rigid": 1, "assembled": 0, "liquid": 0},
             "checks": {"rigid": True, "assembled": False, "liquid": False}}] * 3
    assert replay(rows)["tribes"] == 1.0
    assert replay(rows, use_checks=False)["tribes"] == 0.0
    assert replay(rows, use_checks=False)["use_layer"] is False


def test_bootstrap_ci_brackets_the_mean():
    deltas = [(i % 10, float((i * 7919) % 11 < 6)) for i in range(60)]
    lo, hi = bootstrap_ci(deltas, reps=500)
    m = sum(d for _, d in deltas) / len(deltas)
    assert lo <= m <= hi and lo < hi


def test_load_rows_formats(tmp_path):
    jl = tmp_path / "rows.jsonl"
    jl.write_text("\n".join(json.dumps(r) for r in ROWS))
    js = tmp_path / "fit.json"
    js.write_text(json.dumps({"use_layer": True, "items": ROWS}))
    arr = tmp_path / "rows.json"
    arr.write_text(json.dumps(ROWS))
    assert len(load_rows(str(jl))) == len(load_rows(str(js))) == len(load_rows(str(arr))) == 4
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"x": 1}))
    with pytest.raises(ValueError):
        load_rows(str(bad))


def test_cli_replay_report_pick_info(tmp_path, capsys):
    jl = tmp_path / "rows.jsonl"
    jl.write_text("\n".join(json.dumps(r) for r in ROWS))
    assert main(["replay", str(jl)]) == 0
    assert "tribes       0.7500" in capsys.readouterr().out
    assert main(["replay", str(jl), "--mode", "both", "--json"]) == 0
    assert set(json.loads(capsys.readouterr().out)) == {"lite", "full"}
    fit = tmp_path / "fit.json"
    fit.write_text(json.dumps({"mode": "full", "z": 1.0, "use_layer": True, "n": 4, "mean_gain": 0.5, "se": 0.2,
                               "program_score": 0.25, "tribes_score": 0.75, "oracle_score": 1.0,
                               "verifier": {"enabled": True, "won": 3, "lost": 0, "contested": 5},
                               "cost": {"total": {"cost_usd": 0.12, "calls": 9, "prompt_tokens": 10,
                                                  "completion_tokens": 5}}}))
    assert main(["report", str(fit)]) == 0
    out = capsys.readouterr().out
    assert "use layer     True" in out and "verifier      on" in out and "$0.1200" in out
    assert main(["pick", "--rigid", "1", "--assembled", "2", "--liquid", "1"]) == 0
    assert capsys.readouterr().out.strip() == "rigid (vote)"
    assert main(["pick", "--rigid", "1", "--assembled", "-"]) == 0
    assert capsys.readouterr().out.strip() == "rigid (fallback)"
    assert main(["info"]) == 0
    assert "tribes 1.1.0" in capsys.readouterr().out


def test_ledger_prices_and_ratio():
    led = Ledger(prices={"z-ai/glm": (0.1, 0.4)})
    led.count_item()
    led.add("rigid", 1.0, {"openrouter/z-ai/glm": {"prompt_tokens": 1_000_000, "completion_tokens": 0}}, True)
    u = led.add("assembled", 2.0, {"openrouter/z-ai/glm": {"prompt_tokens": 0, "completion_tokens": 1_000_000}}, True)
    assert u["cost_usd"] == pytest.approx(0.4)
    s = led.summary()
    assert s["total"]["cost_usd"] == pytest.approx(0.5) and s["cost_vs_program"] == pytest.approx(5.0)
    led.add("liquid", 0.1, {"unknown/model-xyz": {"prompt_tokens": 5, "completion_tokens": 5}}, False)
    s = led.summary()
    assert s["forms"]["liquid"]["unpriced_calls"] == 1 and s["forms"]["liquid"]["failures"] == 1
    assert price("unknown/model-xyz", 1, 1) is None
    led.reset()
    assert led.summary()["total"]["calls"] == 0
