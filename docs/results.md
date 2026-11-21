# Results

GLM 5.3 Flash as the task model; each optimizer with its official settings; every number is TRIBES minus that
optimizer's own program on the same items, in percentage points.

## At a glance

| benchmark | development · 1.1 | sealed test · 1.0-lite | fresh test · 1.1 |
|---|---|---|---|
| AIME | +31.1 | — | — |
| BIRD | +23.2 | +5.0 | +3.2 |
| NATURAL PLAN | +21.0 | +13.7 | — |
| LiveCodeBench | +20.0 | +13.0 | — |
| LiveBench | +17.4 | — | — |
| HoVer | +12.6 | — | +12.4 |
| ToolHop | +4.7 | +1.3 | +2.2 |
| GPQA | +3.6 | +2.5 | +1.7 |
| HotpotQA | +3.4 | — | +4.2 |
| IFBench | +1.6 | — | — |
| PUPA | +1.2 | — | — |
| BFCL | 0.0 | — | — |
| τ²-bench | 0.0 | — | — |
| **all cells** | **+11.6** (36 cells) | **+7.1** (15 cells) | **+4.7** (15 cells) |

Mean over GEPA, MIPROv2 and SIMBA, in percentage points over each optimizer's own program. Development numbers are post
hoc: the 1.1 components were designed while these outputs were visible, so read them as an upper bound. The two tests
were frozen before they were opened and are the numbers to quote. — : no held-out items for that benchmark in that test.

## Fresh test (TEST-B, TRIBES 1.1)

1,010 new items, used nowhere in development or in the sealed test. The 1.1 policy (per task: `lite` for BIRD,
GPQA and HotpotQA, `full` for HoVer and ToolHop, the do-no-harm switch) and the analysis were pre-registered before
any model saw them, and the items were opened once.

<figure class="tb-figure" markdown>
![TEST-B: TRIBES 1.1 minus the program per benchmark](assets/chart-testb-light.png#only-light)
![TEST-B: TRIBES 1.1 minus the program per benchmark](assets/chart-testb-dark.png#only-dark)
</figure>

| benchmark (test items) | over GEPA | over MIPROv2 | over SIMBA | benchmark mean, 95 % CI |
|---|---|---|---|---|
| HoVer (150) | +12.7 | +8.0 | +16.7 | **+12.4** [+8.9, +16.4] |
| HotpotQA (200) | +7.0 | +3.0 | +2.5 | **+4.2** [+1.8, +6.8] |
| BIRD (300) | 0.0 | +5.0 | +4.7 | **+3.2** [+0.9, +5.7] |
| ToolHop (200) | +3.5 | +3.5 | −0.5 | +2.2 [−0.5, +5.0] |
| GPQA (160) | +0.6 | +4.4 | 0.0 | +1.7 [−1.5, +4.8] |
| **mean** | +4.8 | +4.8 | +4.7 | **+4.7** [+3.4, +6.1] |

Bold: significant (one-sided α = 0.025, Holm over the five benchmarks; the mean: p = 0.0001). Pre-registered
expectation: about +6 pp. On the same items TRIBES 1.0-lite gains +2.5 pp, so 1.1 adds **+2.2 pp** [+1.5, +3.0] over 1.0.
On HoVer the set merge beats merging three samples of the program by **+7.1 pp** [+4.4, +10.2]: the gain is not just
more sampling.

Descriptive, not tested:

- `full` everywhere plus the verifier (the development policy): +5.2 pp [+3.9, +6.5] over the program, half a point
  above the frozen policy.
- The agent on its own is 6.8 pp *below* the program: it helps only inside the selection rule.
- BIRD gains grow with difficulty: +2.4 (simple), +2.9 (moderate), +6.9 pp (challenging). These BIRD items are
  easier than the development ones (programs solve about 56 %), which is why the gain is far below development.

The pre-registration and the full report are in `research/reports/` (`PREREG-TESTB-20261121.md`,
`RESULT-TRIBES11-TESTB-20261121.md`); every number above is in `research/results/testb_result.json`.

## Sealed test (TEST-A, TRIBES 1.0-lite)

Opened once, after the rule and every per-task decision were frozen.

| benchmark (test items) | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| NATURAL PLAN (200) | **+13.5** | **+17.0** | **+10.5** |
| LiveCodeBench (82) | **+11.0** | **+14.6** | **+13.4** |
| BIRD (200) | +2.5 | **+9.0** | +3.5 |
| GPQA (80) | +3.8 | 0.0 | +3.8 |
| ToolHop (200) | +2.5 | +2.0 | −0.5 (1 item of 200) |
| **mean** | **+6.7** | **+8.5** | **+6.1** |

Bold: 95 % confidence interval above zero. No cell has its interval below zero. Mean over the 15 cells: **+7.1 pp**.

## Development (TRIBES 1.1)

13 benchmarks (AIME, GPQA, LiveBench, LiveCodeBench, HotpotQA, HoVer, IFBench, PUPA, BFCL, τ²-bench, NATURAL PLAN,
BIRD, ToolHop) × 3 optimizers = 36 cells, post hoc.

| benchmark | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| AIME | +38.0 | +23.3 | +32.0 |
| BIRD | +28.5 | +15.0 | +26.0 |
| NATURAL PLAN | +24.0 | +18.0 | +21.0 |
| LiveCodeBench | +20.0 | +20.0 | +20.0 |
| LiveBench | +15.3 | +21.4 | +15.6 |
| HoVer | +12.3 | +9.7 | +15.7 |
| ToolHop | +9.0 | +0.5 | +4.5 |
| HotpotQA | +2.7 | +1.7 | +5.7 |
| GPQA | +0.8 | +9.3 | +0.8 |
| IFBench | +2.2 | 0.0 | +2.6 |
| PUPA | +1.7 | 0.0 | +1.8 |
| τ²-bench | 0.0 | — | — |
| BFCL | 0.0 | — | 0.0 |

| | TRIBES 1.1 | 1.0 full | 1.0 lite |
|---|---|---|---|
| over GEPA | +11.9 | +10.1 | +9.3 |
| over MIPROv2 | +10.8 | +8.7 | +8.4 |
| over SIMBA | +12.1 | +9.6 | +8.9 |
| **all 36 cells** | **+11.6** | **+9.5** | **+8.9** |

No cell below the program. What 1.1 adds over 1.0 here: BIRD agents that can run SQL, the set merge on HoVer, the
abstention check on ToolHop, the verifier on AIME, LiveBench and LiveCodeBench, and a per-task choice of `lite` or `full`
(every choice made on selection data). These numbers are post hoc; the per-cell audit and the frozen decisions are in
`research/reports/FABLE-FREEZE-TESTB-20261120.md`.

## FNXL (financial token labeling)

GEPA vs GEPA + TRIBES 1.0 on the FLARE FNXL test (318 sentences):

| | item score | macro-F1 | micro-F1 |
|---|---|---|---|
| GEPA | 0.600 | 0.376 | 0.393 |
| GEPA + TRIBES (full) | 0.605 | **0.437** | **0.459** |
