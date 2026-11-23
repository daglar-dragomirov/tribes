# PeachTrees — research record

This folder is the evidence behind the numbers in the main README: how the 1.0 rule was found, how it was frozen, and
how it was tested once on held-out data. The installable package lives in `src/peachtrees`; this folder is for
transparency, not for import.

## Setup in one paragraph

Task model GLM 5.3 Flash. Three prompt optimizers with their official settings: GEPA, MIPROv2 (auto heavy) and SIMBA.
Thirteen benchmarks: AIME, GPQA, LiveBench, LiveCodeBench, HotpotQA, HoVer, IFBench, PUPA, BFCL, τ²-bench, NATURAL PLAN,
BIRD, ToolHop. Each benchmark has fixed splits: FIT (the optimizer's train set), PARETO (its validation set), DEV
(development) and, where one exists, a sealed TEST. A *cell* is one benchmark × one optimizer; 36 cells in all. For every
cell the three PeachTrees forms were run on FIT, PARETO and DEV, and every number is PeachTrees minus that optimizer's own
program on the same items.

## Timeline

| step | what happened | where |
|---|---|---|
| v0.2 | forms + an LLM judge with a calibrated threshold and a gate: +6.6 pp over the programs (36 cells, DEV) | `reports/ANALYSIS-PEACHTREES-20261110.md` |
| analysis | an offline analysis of every saved per-item output (no model calls) found a simpler rule that beats the judge: drop broken outputs → task check → vote → reviewer, plus a non-inferiority switch per task | `reports/FABLE-ANALYSIS-RESULT-20261119.md`, `fable-replay/` |
| 1.0 frozen | the rule written as code and replayed independently: +9.47 pp on the saved outputs; +9.41 pp after re-running only the outputs that had failed to parse | `rule/peachtrees_v1.py`, `analysis/p2_replay.py`, `results/p2_saved.json`, `results/p2_repaired.json` |
| decisions frozen | the per-task decision (use the layer or not) fixed on FIT + PARETO + DEV *before* the test was opened | `results/frozen_decisions.json`, `results/decisions_PFD.json` |
| sealed test | 15 cells (5 benchmarks with a held-out set × 3 optimizers), opened once: **+7.1 pp**, 7 cells significantly above the program, none significantly below | `analysis/test_v1.py`, `results/test_result.json` |
| FNXL | GEPA vs GEPA + PeachTrees 1.0 on financial token labeling: item score 0.600 → 0.605, apo macro-F1 0.376 → 0.437 | `analysis/fnxl_v1.py`, `results/fnxl_result.json` |
| 1.1 development | the 1.1 components (BIRD agents with `run_sql`, HoVer set merge, ToolHop abstention check, the verifier, a per-task `lite` / `full` choice), every decision on selection data: **+11.6 pp** over the programs on 36 cells (post hoc; 1.0: +9.5) | `reports/FABLE-FREEZE-TESTB-20261120.md` |
| TEST-B (1.1) | 1,010 fresh items (BIRD dev minus Mini-Dev, unused ToolHop, GPQA-main minus Diamond, unused HoVer and HotpotQA test pools), 15 cells, design and analysis pre-registered: **+4.73 pp** [+3.43, +6.07] over the programs; every secondary step confirmed (1.1 − 1.0-lite +2.24; BIRD 1.1 − 1.0-lite +2.56; HoVer merge − reviewer +7.33, − program × 3 +7.11); significant alone: HoVer +12.4, HotpotQA +4.2, BIRD +3.2 | `reports/PREREG-TESTB-20261121.md`, `reports/RESULT-TRIBES11-TESTB-20261121.md`, `results/testb_result.json` |
| 1.2 screens | candidates screened on PARETO + FIT (stratified by whether the 1.1 forms were already right), each adopted only by a pre-fixed gate (pooled weighted gain > 0 and >= 1 se): the agents at reasoning effort high (8 benchmarks), plus 16 steps and one retry for the tool agents (ToolHop, HoVer); the agent with demonstrations was not adopted | `results/frozen_decisions_12.json` |
| TEST-C (1.2) | 1,323 fresh items (unused ToolHop, HoVer, NATURAL PLAN, IFBench and BIRD simple pools, GPQA-extended minus GPQA-main, AIME 2026), 21 cells, design and analysis pre-registered: **+14.32 pp** [+11.92, +16.76] over the programs; every secondary step confirmed (1.2 − 1.1 +2.77; 1.2 − the program at the same reasoning effort +6.40; ToolHop 1.2 − 1.1 +4.06; HoVer 1.2 − 1.1 +5.33); significant alone: AIME 2026 +35.6, HoVer +20.3, NATURAL PLAN +19.3, GPQA-extended +9.2, ToolHop +8.5, BIRD +4.7 (IFBench +2.7 not) | `reports/PREREG-TESTC-20261123.md`, `reports/RESULT-TRIBES12-TESTC-20261123.md`, `results/testc_result.json` |

## Why the test number is lower than the development number

The 1.0 rule was designed after the development outputs had been seen. Cross-validation between FIT and PARETO and a
leave-one-benchmark-out check protect the choice inside the family of rules, not the family itself. The sealed test is
the honest estimate: +7.1 pp against about +11 pp on the same 15 cells in development. The largest drop is BIRD over GEPA
(+20.5 → +2.5), the cell with the strongest winner's curse in the analysis.

## Files

```
rule/peachtrees_v1.py      the research version of the rule, with per-task answer keys and checkers
analysis/p2_replay.py      replays the frozen rule over the saved outputs of the 39 development runs
analysis/test_v1.py        computes the sealed-test table from the test runs and the frozen decisions
analysis/fnxl_v1.py        GEPA vs PeachTrees on FNXL
results/*.json             every number quoted in the README, per cell, with confidence intervals
reports/                   the v0.2 analysis, the inputs given to the offline analysis and its full report
fable-replay/              the offline analysis: its scripts and logs
```

The analysis scripts read the saved per-item outputs of the experiment runs (paths of the original run store). The runs
themselves, the experiment harness and the benchmark data are not part of this repository; the sealed test sets are
deliberately not published.
