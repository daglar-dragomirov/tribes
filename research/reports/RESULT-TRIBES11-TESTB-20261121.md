# TRIBES 1.1 — TEST-B result (2026-11-21)

Pre-registered in `docs/PREREG-TESTB-20261121.md` (commit e96f4313, amendments dadd7df9 and d62249ef, all before the
analysis ran). Analysis `scripts/tribes_testb_v11.py`, run once: `docs/tribes-11/testb/testb_result.json` and `.log`.
15 cells, 1,010 fresh items, no missing cell, 23 nodes, 13.7 USD.

## Primary endpoint — confirmed

Mean over 15 cells of 1.1 − program: **+4.73 pp**, 95 % CI [+3.43, +6.07], one-sided p = 0.0001.
(Pre-registered expectation +6.1, range +4.5 .. +8.)

## Secondary, fixed sequence — every step confirmed

| step | mean (pp) | 95 % CI |
|---|---|---|
| S1 1.1 − 1.0-lite, all cells | +2.24 | [+1.48, +3.03] |
| S2 BIRD: 1.1 − 1.0-lite | +2.56 | [+0.33, +4.89] |
| S3a HoVer: merge − reviewer | +7.33 | [+4.89, +10.22] |
| S3b HoVer: merge − program × 3 merged | +7.11 | [+4.44, +10.22] |

## Per benchmark (1.1 − program, Holm at 0.025)

| benchmark | mean (pp) | 95 % CI | Holm |
|---|---|---|---|
| HoVer | +12.44 | [+8.89, +16.44] | yes |
| HotpotQA | +4.17 | [+1.83, +6.83] | yes |
| BIRD | +3.22 | [+0.89, +5.67] | yes |
| ToolHop | +2.17 | [−0.50, +5.00] | no |
| GPQA | +1.67 | [−1.46, +4.79] | no |

## Cells (accuracy %, n; gain = 1.1 − program)

| cell | n | program | 1.0-lite | 1.0-full | 1.1 | gain | 1.1-full |
|---|---|---|---|---|---|---|---|
| GEPA BIRD | 300 | 56.0 | 55.7 | 57.0 | 56.0 | 0.00 | 56.7 |
| MIPROv2 BIRD | 300 | 53.7 | 55.0 | 57.0 | 58.7 | +5.00 | 59.0 |
| SIMBA BIRD | 300 | 58.0 | 59.0 | 59.3 | 62.7 | +4.67 | 62.7 |
| GEPA ToolHop | 200 | 45.5 | 46.5 | 47.5 | 49.0 | +3.50 | 49.0 |
| MIPROv2 ToolHop | 200 | 71.0 | 72.5 | 73.5 | 74.5 | +3.50 | 74.5 |
| SIMBA ToolHop | 200 | 73.5 | 73.5 | 73.0 | 73.0 | −0.50 | 73.0 |
| GEPA GPQA | 160 | 72.5 | 73.1 | 73.1 | 73.1 | +0.62 | 73.1 |
| MIPROv2 GPQA | 160 | 69.4 | 73.8 | 75.6 | 73.8 | +4.37 | 75.6 |
| SIMBA GPQA | 160 | 70.6 | 70.6 | 72.5 | 70.6 | 0.00 | 72.5 |
| GEPA HoVer | 150 | 74.7 | 79.3 | 79.3 | 87.3 | +12.66 | 87.3 |
| MIPROv2 HoVer | 150 | 73.3 | 73.3 | 73.3 | 81.3 | +8.00 | 81.3 |
| SIMBA HoVer | 150 | 72.7 | 83.3 | 83.3 | 89.3 | +16.66 | 89.3 |
| GEPA HotpotQA | 200 | 65.0 | 72.0 | 71.5 | 72.0 | +7.00 | 71.5 |
| MIPROv2 HotpotQA | 200 | 70.0 | 73.0 | 74.5 | 73.0 | +3.00 | 74.5 |
| SIMBA HotpotQA | 200 | 67.0 | 69.5 | 70.0 | 69.5 | +2.50 | 70.5 |

Dead rows after the transport repair: 1 of 9,090 rows of the three forms (SIMBA GPQA, assembled).

## Descriptive (not tested)

- 1.0-lite − program on the same items: +2.49 [+1.16, +3.84]; 1.1-full − program: +5.18 [+3.94, +6.45];
  1.1 − 1.1-full: −0.45 [−0.90, 0.00] — the ladder's cheaper lite rung cost about half a point here (GPQA, HotpotQA).
- 1.0-full − 1.0-lite: +0.69 [+0.14, +1.23]; full − lite on the 1.1 forms: +1.95 [+1.21, +2.71].
- The agent alone − program: −6.79 [−8.72, −4.81]: the agent is not a better program; it helps only inside the rule.
- BIRD by difficulty (1.1 / 1.0-lite − program): simple +2.4 / +0.4 (84 items), moderate +2.9 / +0.4 (182),
  challenging +6.9 / +2.9 (34).

## Reading (as fixed in advance)

The primary result (+4.7) lies in the pre-registered "confirms 1.1" band (+4 .. +8) and clearly above 1.0-lite on the
same items (+2.5). HoVer is clearly positive (+12.4) and its merge beats a compute-matched program × 3 merge (+7.1).
BIRD is positive and beats 1.0-lite, but far below the development gain (+3.2 vs +23 on DEV, expected +14.8): the dev
items are easier for the programs and the gains grow with difficulty; the full-dev gold is also noisier. ToolHop and GPQA
are positive but not significant at these n, as stated in advance. TEST-A (1.0-lite, +7.1), TEST-B and the development
table remain three separate results.
