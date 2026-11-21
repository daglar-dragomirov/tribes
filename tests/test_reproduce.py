"""The published development table is reproduced from the saved per-item rows with the package alone (no model call).

research/results/rows-dev-cells.jsonl.gz holds, per cell, role and item, the frozen rule's answer-key hashes, the
label-free checker results and the scores of the three forms (PARETO / FIT / DEV; TEST is not included)."""
import json
from pathlib import Path

import pytest

from tribes.replay import load_rows, replay_protocol

R = Path(__file__).resolve().parents[1] / "research" / "results"
ROWS = R / "rows-dev-cells.jsonl.gz"
pytestmark = pytest.mark.skipif(not ROWS.exists(), reason="research data not in this checkout")
# three cells whose last parse-failure repair runs finished after p2_repaired.json was written
LATE_REPAIRS = {"j6a", "ptsa", "pt1l"}


@pytest.fixture(scope="module")
def rows():
    return load_rows(str(ROWS))


@pytest.mark.parametrize("mode", ["full", "lite"])
def test_switch_decisions_and_selection_statistics_match_p2(rows, mode):
    ref = {c["name"]: c[mode] for c in json.loads((R / "p2_repaired.json").read_text())["cells"]}
    got = replay_protocol(rows, mode=mode)
    assert set(got) == set(ref)
    for cell, x in got.items():
        assert x["use_layer"] == ref[cell]["use_pi"], cell
        assert x["select_mean"] == pytest.approx(ref[cell]["pf_mean"], abs=1e-5), cell
        assert x["select_se"] == pytest.approx(ref[cell]["pf_se"], abs=1e-5), cell
        if cell not in LATE_REPAIRS:
            assert x["report_gain"] == pytest.approx(ref[cell]["dev_gain"], abs=1e-5), cell


def test_final_table(rows):
    final = json.loads((R / "p2_final.json").read_text())
    for mode in ("full", "lite"):
        got = replay_protocol(rows, mode=mode)
        for cell, x in got.items():
            assert x["report_gain"] == pytest.approx(final[mode][cell]["report_gain"], abs=1e-9), (mode, cell)
    main = [x for x in replay_protocol(rows, mode="full").values() if x["opt"] != "gepa1"]
    assert len(main) == 36
    assert 100 * sum(x["report_gain"] for x in main) / 36 == pytest.approx(9.50, abs=0.01)
