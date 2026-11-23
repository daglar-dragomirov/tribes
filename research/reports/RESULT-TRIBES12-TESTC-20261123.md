# TRIBES 1.2 — TEST-C result (2026-11-23)

Pre-registered in `docs/PREREG-TESTC-20261123.md` (commit 32bcc758, before any model saw a TEST-C item). Analysis
`scripts/tribes_testc_v12.py`, run once on complete data: `docs/tribes-12/testc/testc_v12_result.json` (sha256
0730dfe5…9f04) and `.log`. 21 cells, 1,323 fresh items (AIME 2026 shared by its three cells), no missing cell, 21 T1
nodes + 4 transport repairs (CR1PTMTH, CR1J6V, CR1J6A, CR1J6I), about 34 USD (account balance; estimate 32 + 8 %).
Model `z-ai/glm-5.3-flash` via open-inference in every arm.

## Primary endpoint — confirmed

Mean over 21 cells of 1.2 − program: **+14.32 pp**, 95 % CI [+11.92, +16.76], one-sided p = 0.0001.
(Pre-registered expectation about +8 .. +10; TEST-B, 1.1: +4.73.)

## Secondary, fixed sequence — every step confirmed

| step | mean (pp) | 95 % CI | p |
|---|---|---|---|
| S1 1.2 − 1.1, all cells | +2.77 | [+1.26, +4.32] | 0.0002 |
| S2 1.2 − the program at effort high (compute-matched control), all cells | +6.40 | [+4.34, +8.46] | 0.0001 |
| S3 ToolHop: 1.2 − 1.1 | +4.06 | [+1.01, +7.45] | 0.0068 |
| S4 HoVer: 1.2 − 1.1 | +5.33 | [+2.33, +8.33] | 0.0001 |

## Per benchmark (1.2 − program, Holm over seven at 0.025)

| benchmark | 1.2 − program | 95 % CI | Holm | 1.1 − program | control − program |
|---|---|---|---|---|---|
| AIME 2026 | +35.56 | [+24.44, +47.78] | yes | +33.33 | +22.22 |
| HoVer | +20.33 | [+16.00, +25.00] | yes | +15.00 | +0.67 |
| NATURAL PLAN | +19.33 | [+13.33, +26.00] | yes | +18.00 | +10.67 |
| GPQA-extended | +9.19 | [+2.05, +16.38] | yes | +5.05 | +14.36 |
| ToolHop | +8.46 | [+4.72, +12.50] | yes | +4.40 | +1.70 |
| BIRD simple | +4.67 | [+1.33, +8.00] | yes | +4.00 | +1.67 |
| IFBench | +2.69 | [−0.20, +5.93] | no (p 0.035) | +1.02 | +4.13 |

## Cells (accuracy %; control = the program at effort high)

| cell | n | program | control | 1.1 | 1.2 | 1.2 − program | agent 1.2 | reviewer 1.2 |
|---|---|---|---|---|---|---|---|---|
| GEPA ToolHop | 99 | 71.7 | 70.7 | 78.8 | 83.8 | +12.1 | 79.8 | 77.8 |
| MIPROv2 ToolHop | 98 | 62.2 | 64.3 | 64.3 | 68.4 | +6.1 | 70.4 | 69.4 |
| SIMBA ToolHop | 98 | 70.4 | 74.5 | 74.5 | 77.6 | +7.1 | 72.4 | 79.6 |
| GEPA HoVer | 100 | 64.0 | 67.0 | 83.0 | 87.0 | +23.0 | 72.0 | 76.0 |
| MIPROv2 HoVer | 100 | 70.0 | 73.0 | 84.0 | 89.0 | +19.0 | 73.0 | 78.0 |
| SIMBA HoVer | 100 | 72.0 | 68.0 | 84.0 | 91.0 | +19.0 | 81.0 | 82.0 |
| GEPA AIME 2026 | 30 | 60.0 | 93.3 | 100.0 | 96.7 | +36.7 | 96.7 | 96.7 |
| MIPROv2 AIME 2026 | 30 | 56.7 | 80.0 | 93.3 | 100.0 | +43.3 | 96.7 | 100.0 |
| SIMBA AIME 2026 | 30 | 66.7 | 76.7 | 90.0 | 93.3 | +26.7 | 100.0 | 93.3 |
| GEPA NATURAL PLAN | 50 | 78.0 | 84.0 | 94.0 | 96.0 | +18.0 | 94.0 | 92.0 |
| MIPROv2 NATURAL PLAN | 50 | 78.0 | 88.0 | 100.0 | 100.0 | +22.0 | 98.0 | 98.0 |
| SIMBA NATURAL PLAN | 50 | 82.0 | 98.0 | 98.0 | 100.0 | +18.0 | 96.0 | 98.0 |
| GEPA IFBench | 50 | 89.2 | 95.6 | 92.6 | 96.9 | +7.7 | 90.9 | 96.9 |
| MIPROv2 IFBench | 50 | 88.7 | 94.0 | 88.7 | 88.7 | 0.0 | 94.0 | 93.0 |
| SIMBA IFBench | 50 | 92.9 | 93.5 | 92.5 | 93.2 | +0.3 | 95.5 | 93.2 |
| GEPA BIRD simple | 100 | 67.0 | 67.0 | 72.0 | 72.0 | +5.0 | 72.0 | 72.0 |
| MIPROv2 BIRD simple | 100 | 75.0 | 80.0 | 78.0 | 80.0 | +5.0 | 77.0 | 80.0 |
| SIMBA BIRD simple | 100 | 68.0 | 68.0 | 72.0 | 72.0 | +4.0 | 73.0 | 72.0 |
| GEPA GPQA-extended | 33 | 66.7 | 75.8 | 78.8 | 78.8 | +12.1 | 81.8 | 78.8 |
| MIPROv2 GPQA-extended | 33 | 66.7 | 78.8 | 69.7 | 72.7 | +6.1 | 78.8 | 72.7 |
| SIMBA GPQA-extended | 32 | 59.4 | 81.2 | 59.4 | 68.8 | +9.4 | 71.9 | 65.6 |

MIPROv2 IFBench: the 1.1 do-no-harm switch keeps the program there (unchanged in 1.2), so 1.1 = 1.2 = program.
Transport-repaired rows were laid over the T1 rows by uid (GEPA HoVer 35, GEPA AIME 2, GEPA IFBench 5, MIPROv2 ToolHop 1).

## Descriptive (not tested)

- 1.1 − program on TEST-C: +11.54 [+9.10, +14.02]; the program at effort high − program: +7.92 [+5.33, +10.54].
- The 1.2 agent alone − program: +12.37 [+9.69, +15.02]; the 1.2 reviewer alone: +12.38 [+9.90, +14.89]. With reasoning
  effort high the agent is now a better program on its own (on TEST-B, at effort low, it was −6.8); the item rule adds
  about two points on top.
- Where the gain comes from: on HoVer, ToolHop and BIRD the control gains almost nothing (+0.7, +1.7, +1.7) — the layer
  is the gain. On GPQA-extended (+14.4 vs +9.2) and IFBench (+4.1 vs +2.7) the program at effort high alone does better
  than 1.2, whose program form keeps effort low: these two benchmarks reward more thinking, not more forms. On AIME and
  NATURAL PLAN both help; 1.2 is ahead (+35.6 vs +22.2, +19.3 vs +10.7).
- Lesson for 1.3 (development data from now on): give the program form itself the higher effort where the control
  beats the layer (GPQA, IFBench), screened on development data and confirmed on a new test.

## Reading against the pre-registration

The primary result (+14.3) is clearly above TEST-B's +4.7 and S1 holds: 1.2 improves on 1.1. S2 holds: the gain is not
only the extra reasoning effort. Six of seven benchmarks are significant after Holm; IFBench is not (as expected at
n = 150). GPQA-extended and AIME 2026 were expected not to reach significance on their own and did.
TEST-A, TEST-B and TEST-C remain three separate tables; TEST-C is development data for later versions from now on.
