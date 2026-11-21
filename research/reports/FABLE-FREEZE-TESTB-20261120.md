# TRIBES 1.1 - audit, freeze and the confirmatory test TEST-B (Fable 5.2), 2026-11-20

Scope: (A) audit of the 1.1 development evidence and the exact freeze per cell; (B) design and pre-registration of the
one-time confirmatory test TEST-B on fresh items; (C) execution plan with the existing tools and a cost estimate;
(D) what is still worth doing before the freeze.

Method: read-only. An independent per-item replay of all 35 development cells on the server (PARETO, FIT, DEV), built
from the same saved rows as `/root/pt-export/table11.py`, plus counts of the unused item pools (ids only). No model call,
no experiment, nothing in the repository, git, orx, contracts or runs was changed. No sealed item content was opened or
printed (only ids were read to count what is unused). Helpers: `/root/fable-freeze/` (server) and
`scratchpad\fable\freeze\` (local: `audit11.py`, `sum11.py`, `ladder.py`, `pools.py`, `costs.py`, outputs
`out_sum11.txt`, `out_ladder.txt`, `out_costs.txt`, `frozen_decisions_11_draft.json`).

Status of numbers: "measured" = replayed from saved rows, file named; DEV numbers are post hoc; P+F = PARETO + FIT pooled.
"est." = my estimate. Gains are pp over the optimizer's program on the same items. Cell order: GEPA / MIPROv2 / SIMBA.

---------------------------------------------------------------------------------------------------------------------

## 0. Bottom line

1. **The 1.1 table is correct and clean.** My independent replay reproduces every one of the 35 cells of
   `table11_final.json` exactly (1.0-full +9.50, 1.1 +11.77; `out_sum11.txt`, section A - no mismatch). No leakage:
   the verifier has DEV records only in the cells whose gate passed on P+F; the gate, the switch and the BIRD decision
   read P+F only; the HoVer merge has no fitted parameter and its metric equals the worker's own score. Six caveats are
   listed in section 1.2; none changes a number.
2. **One real finding the table hides: on BIRD the vote now hurts.** With the run_sql agents, full minus lite is
   -0.33 +- 1.67 on P+F and -2.67 +- 1.04 on DEV (9 items won, 25 lost). The reviewer alone is the better and cheaper
   policy there (DEV +28.5 / +15.0 / +26.0 against the table's +27.5 / +14.5 / +22.0).
3. **Freeze 1.1 as a ladder decided on P+F only** (section 2): lite on BIRD, GPQA, HotpotQA, IFBench, PUPA, BFCL;
   full (vote / set merge) on HoVer, ToolHop, NATURAL PLAN; full + verifier on AIME (GEPA, SIMBA), LiveBench (x3),
   LiveCodeBench (x3). DEV mean over the 36 cells: **+11.64** (table policy "full everywhere": +11.77; 1.0-full +9.50;
   1.0-lite +8.91) - the same accuracy within noise at a lower cost, and every choice has a P+F reason. The table's
   policy is kept as the nested secondary "1.1-full".
4. **Fresh pools: four benchmarks are ready on the server, the most important one is not.** Ready and untouched:
   ToolHop (495 unused queries), GPQA (160 unused GPQA-main items outside Diamond), HoVer (2,133) and HotpotQA
   (35,878) in the artifact's test pools outside the 300 ids opened for v0.2, NATURAL PLAN (2,100). **Not on the
   server: BIRD beyond Mini-Dev (all 500 Mini-Dev items are used), a later LiveCodeBench release (all 342 problems are
   used), AIME 2026, a later LiveBench release.** PUPA is exhausted (664 of 664 rows assigned) and the HotpotQA / HoVer /
   IFBench / PUPA "sealed" sets were opened on 2026-10-26 for v0.2 - not clean, not used.
5. **TEST-B = 15 core cells (BIRD, ToolHop, GPQA, HoVer, HotpotQA x 3 optimizers) + 5 extension cells (AIME 2026 over
   GEPA and SIMBA, later LiveBench x 3) if their sources can be obtained before the pre-registration.** One download
   needs the user's go-ahead: BIRD `dev.json` (the databases are already on the server). Est. cost 22 USD (+8 % for
   retries = 23.7), under the 25 USD budget. LiveCodeBench is left out: no fresh pool, and one cell cost 3.4-4.5 USD on
   TEST-A for two forms.
6. **Power (est.)**: primary endpoint se 0.8-0.9 pp; a true +3 pp is detected with probability about 0.95; expected
   primary result with the 0.64 shrinkage **+6.1 (core 15 cells) / +8.5 (20 cells)**; 1.1 minus 1.0-lite expected
   +2.6 / +2.8 with se 0.5.
7. **Before the freeze: nothing paid. Freeze now.** The checker-triggered retries are worth est. +0.3 pp on the TEST-B
   mean for about 1 USD plus a new worker version and a new gate; the IFBench / PUPA checkers cannot be confirmed on a
   clean split. Three zero-cost items must be done at the freeze (section 5).

---------------------------------------------------------------------------------------------------------------------

## 1. Audit of the 1.1 development evidence

### 1.1 What was checked and how

`audit11.py` rebuilds, per item and role, from the same sources as `table11.py` (P3-repaired rows first, S2 rows for the
BIRD agents, `verify-*.jsonl` of the S3 runs listed in `/root/s3_state.json` and `/root/s3b_state.json` plus run
e0a68728): the program, 1.0-lite, 1.0-full, and the 1.1 pieces separately (new forms, abstention filter, merge,
verifier). BIRD queries of the new agents were re-executed locally. `sum11.py` compares with `table11_final.json`.

| check | result | file |
|---|---|---|
| per-cell DEV gain of 1.0-full and 1.1, all 35 cells | identical to `table11_final.json` (tolerance 1e-4), means 9.50 and 11.77 | `out_sum11.txt` A, H |
| the switch (do-no-harm, z = 1) | computed on P+F only; off in BFCL x2, IFBench-MIPROv2, PUPA-MIPROv2 (+ tau2), as in 1.0 | A |
| the verifier gate | recomputed from `verify-PARETO/FIT.jsonl` only; 11 cells pass (AIME G+S, GPQA S, LiveBench x3, HotpotQA S, LCB x3, BIRD G) | B |
| the verifier on DEV | `verify-DEV.jsonl` exists only for those 11 cells; non-gated cells have no DEV record at all | B |
| HoVer metric | the table's own subset metric equals the worker's saved score for single forms (0-1 differing rows per 450, never in the merge's favour); the program baseline uses the saved score | D |
| HoVer cap | the program's own maximum is 24 titles in every cell (max over items = 24; mean 17-18) | D |
| ToolHop filter | 147 flagged outputs (37 on P+F, 110 on DEV), 0 correct | E |
| BIRD | the program's rows are the original cell's rows in both arms; old agents for 1.0, S2 agents for 1.1 | `table11.py` lines 142-169 |

### 1.2 Caveats (none is a leak; state them in the paper)

1. **Verifier, design level.** The gate is clean, but the verifier's protocol (contested items only, evidence gate, 2 of
   3 votes) was designed on 2026-11-19 from judge records that included DEV. Its DEV numbers are "post hoc", like all
   DEV numbers. Encouraging: the 11 gated cells show no shrinkage from P+F to DEV (DEV: 50 switches won, 7 lost, mean
   +2.68 pp per cell; `out_sum11.txt` B).
2. **Verifier, the cell gate is weak for small n.** "won - lost >= 2 and gain > 0.5 pp" passes on 2 won / 0 lost
   (GPQA-SIMBA: DEV -0.85; BIRD-GEPA) and on 5 won / 3 lost (LiveBench-MIPROv2). It stays frozen as it is; the ladder
   in section 2 adds a pooled test per benchmark, which removes exactly the three weakest cells.
3. **AIME DEV is 30 problems x 5 repeats.** The verifier's 13 / 0 and 9 / 0 switches are clustered by problem; the cell
   intervals are wide ([+27, +49] for GEPA, `table11_final.log`).
4. **Verifier base.** The verifier was run against the 1.0 item rule without the ToolHop abstention filter; where its
   base differs from the 1.1 pick (ToolHop 3 / 1 / 2 items, BIRD 2 / 0 / 1) the table ignores the verdict. This is the
   conservative choice; the TEST-B script must do the same.
5. **ToolHop abstention filter.** The regular expression was written after reading outputs of all three splits. Its
   measured effect is one or two items per cell (full: P+F 0 / 0 / +1.0, DEV +1.0 / 0 / 0). It enters 1.1 as a declared
   checker ("every query has an answer"), not through a gate. Honest wording: no measurable gain, no harm.
6. **HoVer merge.** Cap 24 is the program's own budget (7 + 7 + 10 passages), the form order is fixed, nothing is tuned,
   P+F and DEV agree (+7.04 +- 0.80 and +5.78 +- 0.87 over the reviewer, pooled). Two limits: the metric is recall-only,
   and part of the gain is "more retrieval inside the same 24 slots" - the compute-matched control (program x 3) is the
   answer and must be repeated on TEST-B. The public package's default (`doc_set(cap="program")`, the program's count
   on the item, 17-18 on average) is NOT the evaluated rule (fixed 24); the earlier replay had cap 18 lower by 1-3 pp.
7. **P+F is the optimizers' own data.** FIT trained the programs and PARETO selected them, so the program is flattered
   on P+F and gains over it are biased downward there. This makes the switch conservative; comparisons between layer
   policies (full vs lite, verifier vs none) are much less affected.
8. Not in 1.1 (and not in the table): the IFBench prompt-parsed checker and the PUPA detail count. On IFBench and PUPA
   1.1 is identical to 1.0. Minor: `comp` in `table11.py` is dead code; tau2 is counted as 0; there is no BFCL cell
   over MIPROv2 (35 cells + tau2 = 36).

### 1.3 Components, measured (P+F decides, DEV post hoc)

| component | P+F evidence | DEV (post hoc) | source |
|---|---|---|---|
| BIRD run_sql agents (S2), 1.0-full rule, new vs old | +12.67 +- 2.79, 47 won / 9 lost | +11.33 +- 2.40 | `/root/pt-export/s2_gate_pf.log`, `s2_gate_dev.log` |
| HoVer merge vs reviewer, pooled 3 cells | +7.04 +- 0.80, 97 / 2 | +5.78 +- 0.87, 52 / 0 | `out_ladder.txt` |
| HoVer merge vs program x 3 merged | +9.6 / +4.7 / +9.1 | +7.3 / +3.0 / +10.3 | task brief (hover_control.py output) |
| verifier, 18 cells stage 1 + BIRD x3 | 62 won / 14 lost (21 cells) | gated cells: 50 / 7, +2.68 pp per cell | `out_sum11.txt` B |
| ToolHop abstention filter (on full) | 0 / 0 / +1.0 | +1.0 / 0 / 0 | `out_sum11.txt` E |
| vote (full - lite), per benchmark | section 2.1 | section 2.1 | `out_ladder.txt` |

---------------------------------------------------------------------------------------------------------------------

## 2. The freeze of 1.1

### 2.1 The ladder: lite or full per task, decided on P+F only

Rule (fixed in `ladder.py` before its output was read): per benchmark, pooled over its optimizer cells and clustered by
item, start at lite; test the upgrades in cost order - full (vote; on HoVer the set merge), then full + verifier (the
verifier acts only in the cells whose frozen cell gate passed). An upgrade is accepted iff its pooled P+F mean
difference against the currently accepted rung is > 0 and >= 1 standard error. The do-no-harm switch (z = 1, P+F) is
then applied per cell to the chosen policy.

| benchmark | full vs lite on P+F (won / lost) | verifier rung on P+F | decision | DEV post hoc of the accepted / rejected step |
|---|---|---|---|---|
| AIME | +2.96 +- 1.01 (8 / 0) | vs full +2.22 +- 0.88 (6 / 0) | **full + verifier** | +2.44, then +4.89 |
| LiveBench | +0.67 +- 0.67 (14 / 9), borderline | vs full +1.05 +- 0.38 (25 / 7) | **full + verifier** | +1.29, then +1.59 |
| LiveCodeBench | 0 (no answer key, the vote cannot fire) | vs lite +3.12 +- 0.93 (16 / 1) | **full + verifier** | +2.67 |
| HoVer | +7.04 +- 0.80 (97 / 2) (merge) | - | **full (merge)** | +5.78 |
| ToolHop | +2.33 +- 0.98 (7 / 0) | none gated | **full** | +0.50 |
| NATURAL PLAN | +0.33 +- 0.33 (1 / 0), borderline | - | **full** (a tie in practice) | -0.17 |
| BIRD | -0.33 +- 1.67 (11 / 12) | vs lite +0.33 +- 1.74 | **lite** | full -2.67 +- 1.04 (9 / 25) |
| GPQA | -1.85 +- 1.22 (5 / 10) | vs lite -1.11 +- 1.34 | **lite** | full +2.54 +- 1.46 (opposite sign) |
| HotpotQA | +0.15 +- 0.35 (11 / 9) | vs lite +0.37 +- 0.38 | **lite** | full +0.89 +- 0.47 |
| IFBench, PUPA, BFCL | 0 | - | **lite** | 0.1 / -0.1 / +1.0 |

Source: `out_ladder.txt`. Candid notes: (i) LiveBench and NATURAL PLAN pass at z = 1.0 exactly - a tie; the choice
changes cost, not accuracy. (ii) GPQA is a coin: P+F (GPQA-main) and DEV (Diamond) disagree in sign; lite is the cheap
side of the coin, and the TEST-B items come from GPQA-main, the P+F population. (iii) HotpotQA gives up about 1 pp of
post hoc DEV. (iv) Three cells whose own verifier gate passed do not deploy it, because their benchmark's pooled test
fails: BIRD-GEPA, GPQA-SIMBA (DEV -0.85), HotpotQA-SIMBA (DEV +0.33).

### 2.2 TRIBES 1.1 per cell (the freeze)

Common to every cell: forms unchanged from 1.0 (R = the program, A = reviewer over the program's draft, L = agent);
liveness; task checker where one exists (NATURAL PLAN validators, LiveCodeBench public tests, BIRD "query runs", ToolHop
"an abstention is not an answer"); parse-failure retry 3 in every arm; worker `fieldsuite_worker_v92.py`
(sha256 d8decbd5...c6aa); item rule `peachtrees_v1.py` (sha256 ee450df5...3a9a). Verifier = v92 `verifier_v2`, 6
iterations, 3 votes, contested items only, verdict applied only when its base equals the item rule's pick.

| benchmark | mode | new in 1.1 | verifier deployed | switch G / M / S (P+F gain +- se) | DEV 1.1 G / M / S | DEV 1.0-full |
|---|---|---|---|---|---|---|
| AIME | full | verifier | G, S (M: gate failed 2 / 1) | on / on / on (+30.0 +- 4.9, +22.2 +- 5.4, +36.7 +- 5.4) | +38.0 / +23.3 / +32.0 | +29.3 / +23.3 / +26.0 |
| LiveBench | full | verifier | G, M, S | on x3 (+10.6, +13.0, +10.5; se ~2) | +15.3 / +21.4 / +15.6 | +14.8 / +19.3 / +13.5 |
| LiveCodeBench | full | verifier | G, M, S | on x3 (+23.1, +16.9, +20.6; se ~3.3) | +20.0 / +20.0 / +20.0 | +17.0 / +17.0 / +18.0 |
| HoVer | full = set merge, cap 24, order A, R, L | merge | never (rubric family) | on x3 (+16.0, +12.2, +15.3; se ~1.7) | +12.3 / +9.7 / +15.7 | +6.7 / +3.7 / +10.0 |
| ToolHop | full | abstention checker | no (gates failed) | on x3 (+9.0, +6.0, +4.0; se ~3.3) | +9.0 / +0.5 / +4.5 | +8.0 / +0.5 / +4.5 |
| NATURAL PLAN | full | nothing | no | on x3 (+16, +18, +19; se ~3.9) | +24.0 / +18.0 / +21.0 | same |
| BIRD | **lite**, agents with `run_sql` | run_sql; lite instead of full | no (G passed its cell gate; rung rejected) | on x3 (+14.0, +20.0, +15.0; se ~5.2) | +28.5 / +15.0 / +26.0 | +18.5 / +2.5 / +6.5 |
| GPQA | **lite** | lite instead of full | no (S passed its cell gate; rung rejected) | on x3 (+7.8, +7.8, +10.0; se ~4.5) | +0.8 / +9.3 / +0.8 | +5.1 / +8.5 / +5.1 |
| HotpotQA | **lite** | lite instead of full | no (S passed; rung rejected) | on x3 (+4.2 +- 1.3, +1.6 +- 1.1, +4.4 +- 1.2) | +2.7 / +1.7 / +5.7 | +4.0 / +3.0 / +5.7 |
| IFBench | lite | nothing | never | on / **off** / on (+0.5 +- 0.7, -2.3 +- 1.0, +0.3 +- 0.7) | +2.2 / 0 / +2.6 | +2.2 / 0 / +2.9 |
| PUPA | lite | nothing | never | on / **off** / on (+0.9 +- 0.7, -2.7 +- 1.4, +0.5 +- 0.8) | +1.7 / 0 / +1.8 | same |
| BFCL | program | nothing | never | **off** / - / **off** (-6.1 +- 3.2, -3.0 +- 2.3) | 0 / - / 0 | same |
| tau2 | program | nothing | never | off (as in 1.0) | 0 | 0 |

Means over the 36 cells, DEV, post hoc (`out_ladder.txt`): **1.1 (this freeze) +11.64** (GEPA +11.89, MIPROv2 +10.81,
SIMBA +12.13); 1.1-full (the table's policy) +11.77; 1.1-lite everywhere +10.06; 1.0-full +9.50; 1.0-lite +8.91.
Machine-readable draft: `scratchpad\fable\freeze\frozen_decisions_11_draft.json` (36 entries: use_layer, mode,
verifier, run_sql, merge, abstention checker, P+F gain and se).

Recommendation: freeze the ladder policy as "TRIBES 1.1" and the table's policy as the nested secondary "1.1-full".
If the main session prefers to keep the already reported +11.77 as the headline, the alternative is to freeze
"1.1-full" as primary and report the ladder as secondary; the TEST-B runs are the same in both cases, only the
pre-registered primary policy differs. This must be decided before the pre-registration commit, not after.

---------------------------------------------------------------------------------------------------------------------

## 3. TEST-B - design and pre-registration

### 3.1 Fresh pools: what exists and what does not (checked on the server, ids and manifests only)

| benchmark | used so far | fresh pool | status |
|---|---|---|---|
| ToolHop | 500 of 995 (50 + 50 + 200 + 200 TEST-A) | **495 unused queries** in `newdata-src-v1/toolhop/data/ToolHop.json` | ready, untouched |
| GPQA | 288 (90 GPQA-main, all 198 Diamond) | **160 unused GPQA-main items outside Diamond** (`gpqa-data-v1/raw/dataset/gpqa_main.csv`); 98 more in `gpqa_extended.csv` only (lower-quality keys - not recommended) | ready; same population as P+F, not Diamond |
| HoVer | 750 roles + 300 ids opened for v0.2 | artifact test pool 2,433 three-hop claims minus the 300 opened = **2,133**; val pool remainder 1,833 | ready (HF cache on the server) |
| HotpotQA | 750 roles + 300 opened for v0.2 | artifact test pool 36,178 minus 300 = **35,878** | ready (HF cache on the server) |
| NATURAL PLAN | 500 | 1,350 trip + 750 meeting unused | ready, but 1.1 = 1.0-full there and TEST-A already covers it |
| BIRD | all 500 Mini-Dev items (`bird/data/manifest.json`: question ids 0-499) | **none on the server.** The full dev set (1,534 questions, same 11 databases - from memory, verify) needs `dev.json`; the databases are already in `MINIDEV/dev_databases` | **needs one download = the user's go-ahead** |
| LiveCodeBench | all 342 problems of test5 + test6 (80 + 80 + 100 + 82) | none on the server; a later release needs a download; older releases are unused but more exposed to training data | not ready, and expensive (3.4-4.5 USD per TEST-A cell for two forms) |
| AIME | 90 older problems + AIME 2025 x 5 | AIME 2026 (30 problems) - not on the server | needs a download; "temporally later", not contamination-free |
| LiveBench math | all 368 cached rows | only if the source has a release newer than the cached one | uncertain |
| PUPA | 664 of 664 rows assigned (111 + 111 + 221 + 221) | none | exhausted |
| IFBench | train pool 14,971 (roles drawn from it); test 294 | test opened for v0.2; 1.1 has no IFBench component | skip |
| HotpotQA / HoVer / PUPA / IFBench "sealed specifications" | `fieldsuite-test-opened-v1/OPENED.json`: opened 2026-10-26, "RIDER v0.2 vs official GEPA" | - | **not clean; never use as a test for 1.1** |
| tau2, BFCL | tau2 sealed 300 unopened; BFCL-lc sealed 40 | - | skip (ceiling / layer off: result = program by construction) |

Files: `out` of `pools.py`; manifests under `.external/fieldsuite-*-data-v1/roles-v1/` and `test-eval-v1/`.

### 3.2 Cells and item counts

| tier | benchmark | cells | n per cell | why it is in | 1.1 component tested |
|---|---|---|---|---|---|
| core | BIRD | G, M, S | 300 | weakest on TEST-A (+5.0); carries the largest 1.1 gain | run_sql agents; lite vs full |
| core | ToolHop | G, M, S | 200 | weak on TEST-A (+1.3) | vote on fresh data, abstention checker |
| core | GPQA (main, non-Diamond) | G, M, S | 160 (all) | weak on TEST-A (+2.5) | lite vs full on fresh data |
| core | HoVer | G, M, S | 150 | never tested for TRIBES | set merge + compute-matched control |
| core | HotpotQA | G, M, S | 200 | never tested for TRIBES | none ("no change, no harm" row); lite vs full |
| extension | AIME 2026 | G, S | 30 problems x 5 | the verifier's strongest cells | verifier |
| extension | LiveBench (later release) | G, M, S | about 120 | verifier gated in all three | verifier |
| out | LiveCodeBench | - | - | no fresh pool; est. 6-7 USD per cell for three forms + verifier | verifier on LCB stays a development result |
| out | NATURAL PLAN, IFBench, PUPA, BFCL, tau2 | - | - | 1.1 = 1.0 there; no clean pool or ceiling | - |

The extension cells are part of the primary endpoint only if their items are materialized and hashed before the
pre-registration commit; otherwise TEST-B is the 15 core cells and the verifier has no confirmatory cell (say so).
If BIRD `dev.json` is not approved, BIRD drops out as well and the main 1.1 component cannot be confirmed - then
postpone TEST-B rather than run it without BIRD.

### 3.3 Selection of items and the manifest

- One builder script (new, modelled on `scripts/prepare_fieldsuite_*_roles_v1.py`), seed **20261120** for every draw:
  sort the unused ids, `random.Random(20261120).sample(ids, n)`. Per benchmark:
  - ToolHop: unused = 995 source ids minus the four role files; rows built exactly as the existing role rows.
  - GPQA: `gpqa_main.csv` minus Diamond minus PARETO / FIT ids = 160, all taken; rows built with `row()` of
    `prepare_fieldsuite_gpqa_roles_v1.py` (same option shuffle by Record ID).
  - HoVer / HotpotQA: the artifact's test pool exactly as in the prepare scripts (same shuffle, same 40 % slice),
    minus `roles-v1/test-ids.json`; sample 150 / 200.
  - BIRD: full dev minus Mini-Dev (match by db_id + normalised question, and by question id where present); before
    any model call drop items whose gold query fails, is empty or exceeds 30 s on the server database (the Mini-Dev
    manifest's own check); then a stratified sample by difficulty that is as close to Mini-Dev's mix as the pool
    allows (fixed in the script; report gains by difficulty). Caveat to state: the full dev gold labels are noisier
    than the corrected Mini-Dev ones - absolute accuracies and gains may be lower for every arm.
  - AIME 2026: all 30 problems x 5 repeats, cluster = problem. LiveBench: all rows of releases later than the cached one.
- Output per benchmark: `.external/fieldsuite-<ds>-data-v1/testb-eval-v1/{DEV.jsonl, FIT.jsonl, PARETO.jsonl,
  manifest.json}` in the layout of `test-eval-v1` (DEV = the TEST-B items; FIT / PARETO = byte copies of roles-v1;
  manifest: `TEST_sha256`, `TEST_n`, FIT / PARETO hashes, seed, source hashes, the sha256 of every item id,
  `disjoint_from: roles-v1, sealed-test-v1, test-opened-v1 = true`).
- The manifest hashes, the builder script and the pre-registration are committed to `main` and mirrored to R2 **before
  any model sees an item**. An "opened once" ledger entry (timestamp, commit, cells) is written when the first run
  starts.

### 3.4 Arms on the same items (nested, no extra selection)

| arm | from which outputs |
|---|---|
| program | R |
| 1.0-lite | A (BIRD: A without run_sql), liveness / checker fallback, the frozen 1.0 switch |
| 1.0-full | R, A, L with the 1.0 rule (BIRD: old agents) |
| **1.1 (primary policy)** | section 2.2 |
| 1.1-full (table policy) | R, A, L, vote everywhere, verifier in the 11 cells of the cell gate - needs the verifier also on BIRD-GEPA and HotpotQA-SIMBA (est. 0.2 USD) |
| components | merge vs reviewer and vs program x 3 (HoVer); full vs lite; verifier vs none; new vs old agents (BIRD); agent alone (tool-matched baseline) |

### 3.5 Endpoints (fixed order)

- **Primary (one):** unweighted mean over the registered TEST-B cells of score(1.1) - score(program). One-sided test
  of "> 0" at alpha = 0.025; 95 % interval from a bootstrap that resamples items within each benchmark (the same items
  serve the benchmark's three cells, so the item is the cluster; AIME: the problem), 10,000 draws, seed 11.
- **Secondary, fixed sequence, each one-sided at 0.025, claims stop at the first failure, the rest is descriptive:**
  1. 1.1 - 1.0-lite, all cells (does the new version add anything to the registered 1.0 result?);
  2. BIRD cells: 1.1 - 1.0-lite (environment grounding);
  3. HoVer cells: merge - reviewer; then merge - program x 3 merged (the forms add evidence beyond more samples);
  4. verifier cells (extension tier): full + verifier - full;
  5. 1.1 - 1.1-full (ladder vs "full everywhere"; two-sided, descriptive);
  6. 1.0-full - 1.0-lite, all cells (the vote's first held-out measurement; two-sided, descriptive).
- Per-benchmark gains of 1.1 over the program: Holm over the benchmarks. Every cell is reported, including ties and
  negative cells; the three tables (TEST-A 1.0-lite +7.1; TEST-B; development) are never merged.
- Also reported, not tested: cost multiple per cell (from `worker-summary.json`), dead rows per arm, gains on the rows
  where every arm produced an output.

### 3.6 Exclusions and infrastructure failures (fixed in advance)

- No item is excluded after the manifest commit. A form without a usable output is handled by the rule itself
  (liveness fallback); if the returned form has no output the item scores 0 for that arm. This is the 1.0 TEST policy.
- A run that stops before completion (budget stop, crash, provider outage) is relaunched as the same frozen node with
  the supported launcher; rows already written are replayed, not re-sampled. A cell is "missing" only if two relaunches
  fail; a missing cell is reported and leaves the mean (stated as such), never replaced.
- Transport errors (HTTP 429 / 5xx / timeout recorded in the row) are repaired once with the existing
  `repair_transport_errors` path, identically for every arm, decided from error counts alone - before any score is
  read. Parse failures are not repaired beyond `parse_retry=3` (they are a property of the arm).
- The analysis script is run once, on complete data. If a defect of the script is found afterwards, both versions of
  the result are published.

### 3.7 Power and expected numbers (estimates; standard deviations from DEV, `out_ladder.txt`)

| benchmark | n | sd of the item mean over 3 cells, 1.1 - program | se | DEV 1.1 (post hoc) | expected = 0.64 x DEV | detectable at Holm (80 %) |
|---|---|---|---|---|---|---|
| BIRD | 300 | 36.8 | 2.1 | +23.2 | **+14.8** | yes (needs about 7.5) |
| ToolHop | 200 | 19.5 | 1.4 | +4.7 | **+3.0** (TEST-A lite: +1.3) | no (needs about 4.9) |
| GPQA | 160 | 28.2 | 2.2 | +3.7 (lite; Diamond) | **+2.3** | no (needs about 7.9) |
| HoVer | 150 | 24.0 | 2.0 | +12.6 | **+8.0** (P+F +14.5: little shrinkage expected, est. +9 .. +12) | yes |
| HotpotQA | 200 | 17.6 | 1.2 | +3.3 | **+2.1** | no (needs about 4.4) |
| AIME 2026 (G, S) | 30 problems | about 27 | about 4.9 | +35.0 | **+22** (wide: +10 .. +30) | yes |
| LiveBench | 120 | 29.2 | 2.7 | +17.4 | **+11.2** | yes |

- Primary endpoint, 15 core cells: se est. **0.82 pp**; minimum detectable effect (80 % power) 2.3 pp; power for a true
  +3 pp about 0.95. Expected: **+6.1** (est. range +4.5 .. +8). With the 5 extension cells: se est. 0.88, expected
  **+8.5**.
- 1.0-lite on the same items, expected: +3.5 (core) / +5.7 (20 cells). Secondary 1 (1.1 - 1.0-lite): expected
  **+2.6 / +2.8**, se est. 0.48, minimum detectable 1.3 pp. It is carried by BIRD and HoVer; on GPQA and HotpotQA 1.1
  is identical to 1.0-lite by construction (difference exactly 0).
- The 0.64 factor is the DEV-to-TEST ratio of 1.0-lite on five benchmarks (+11.1 -> +7.1,
  `research/results/test_result.json`); applying it per benchmark is a convention, not a model. Pre-register the
  numbers of this table as the expected values.
- Honest reading in advance: ToolHop, GPQA and HotpotQA cannot be shown individually at these n; they contribute to the
  mean and to "no harm". A primary result between +4 and +8 with BIRD and HoVer clearly positive confirms 1.1; a result
  near the 1.0-lite number on the same items means the new components did not transfer.

---------------------------------------------------------------------------------------------------------------------

## 4. Execution plan with the existing tools

### 4.1 Node builders (new helper scripts under `/root/rider-helpers/`, copies of today's scripts)

| step | script (copy of) | contract changes against the cell's own contract | cells |
|---|---|---|---|
| T1 forms | `testb_node.py` (from `test_node.py`) | `benchmark.roles_dir` -> `.../testb-eval-v1` (+ manifest hash, `role_files.DEV` = TEST-B hash, `role_sizes.DEV` = n, `evaluation_split` text); `worker` = v92 + its LF sha256; `select`: `forms = [rigid, liquid, assembled]`, `roles = [DEV]`, `forms_only = true`, `parse_retry = 3`, no `replay_from`; **BIRD: `benchmark.agent_run_sql = true`**; `scientific_role = TESTB_ONCE`; `max_workers`, `max_usd` from 4.3 | all |
| T2 old agents | `testb_old_node.py` (from `s2_node.py`, reversed) | BIRD only: the same contract without `agent_run_sql`; `select.replay_from = [T1 worker dir]`, `rerun_forms = [liquid, assembled]` - the program's rows are the T1 rows | BIRD x3 |
| T3 control | `s1c_node.py` pointed at the T1 run | `forms = [rigid2, rigid3]`, `roles = [DEV]` | HoVer x3 |
| T4 verifier | `s3_node.py` with ROLES = DEV pointed at the T1 run (rule text edited: "TEST-B, opened once") | `replay_from = [T1 worker dir]`, `verifier_v2 = true`, `verifier_iters = 6`, `verifier_votes = 3` | deployed: AIME G, S; LiveBench x3. For the 1.1-full secondary only: BIRD-GEPA (over T1 forms), HotpotQA-SIMBA |

All nodes are children of the cell's node, frozen with `commit_node.py` and launched with
`/root/.rider4d-claude/launch_serial_long.sh` (one launcher at a time on the shared checkout, as in `s3b_runner.py`).
Before the first paid node: one dry check per benchmark family that a `testb-eval-v1` contract passes preflight
(HoVer and HotpotQA contracts were never served a test dir; `test_node.py` asserts `role_files.FIT` equality - verify
the key exists in those contracts).

### 4.2 Offline (0 USD), one script `research/analysis/testb_v11.py`, committed and hashed before T1

Derived from `table11.py` with three changes: (1) all decisions are read from the committed
`frozen_decisions_11.json` (switch, mode, verifier, merge, checker) - nothing is recomputed from P+F; (2) sources are
the T1-T4 run directories; gold for the HoVer subset metric is read from the TEST-B `DEV.jsonl`; BIRD queries are
executed locally with `_bird_run` on the same databases; (3) it writes every arm of 3.4 per item, the endpoints of 3.5
with the stratified item bootstrap, and the cost and dead-row tables. The item rule functions are imported from
`peachtrees_v1.py` unchanged; the HoVer merge, the ToolHop filter and the verifier application are the exact code of
`table11.py` (lines 116-131, 174-177, 185-187).

### 4.3 Cost per cell (est., USD)

Unit prices: TEST-A per-item costs for BIRD, ToolHop, GPQA (fresh items, `out_costs.txt`); S2 runs for the run_sql
agents; S1 control runs for extra program samples (0.0006-0.0007 per sample on HoVer); today's S3 runs for the
verifier; MIPROv2 / SIMBA development cells for HoVer, HotpotQA, AIME, LiveBench. **Warning:** the GEPA development
cells' recorded costs (older j6* runs) are 2-7 times lower than what fresh items cost today (GPQA-GEPA assembled:
0.0006 on DEV vs 0.0044 on TEST-A; HoVer program 0.0003 vs 0.0007 in today's control) - GEPA cells are priced at
today's level, not at their old records.

| benchmark | n | per item, three forms G / M / S | extras | est. per cell G / M / S | total |
|---|---|---|---|---|---|
| BIRD | 300 | 0.0028 / 0.0034 / 0.0027 | old agents 0.0015 / 0.0020 / 0.0017; verifier G 0.0006 | 1.47 / 1.62 / 1.32 | 4.4 |
| ToolHop | 200 | 0.0074 / 0.0080 / 0.0076 | - | 1.48 / 1.60 / 1.52 | 4.6 |
| GPQA | 160 | 0.0094 / 0.0045 / 0.0043 (agent est.) | - | 1.50 / 0.72 / 0.69 | 2.9 |
| HoVer | 150 | 0.0051 / 0.0089 / 0.0048 | control 0.0014 / 0.0014 / 0.0012 | 0.98 / 1.55 / 0.90 | 3.4 |
| HotpotQA | 200 | 0.0025 / 0.0017 / 0.0015 | verifier S 0.02 | 0.50 / 0.34 / 0.32 | 1.2 |
| AIME 2026 | 150 rows | 0.0082 / - / 0.0097 | verifier 0.0014 | 1.44 / - / 1.65 | 3.1 |
| LiveBench | 120 | 0.0060 / 0.0042 / 0.0050 | verifier 0.0013-0.0019 | 0.88 / 0.73 / 0.79 | 2.4 |
| **sum** | | | | | **22.0; with 8 % for retries 23.7** |

- Budget control: `max_usd` per node = 1.14 x its estimate, so that the caps sum to 25.0. Core tier alone: 16.5
  (17.8 with retries); if the extension tier is not available, raise HoVer to 200 and ToolHop to 300 items (+3.4).
- If money gets tight, cut in this order (decide before the pre-registration, never after): LiveBench-MIPROv2;
  HotpotQA to 150; GPQA agent form (then no 1.0-full / 1.1-full on GPQA). Never cut BIRD or the HoVer control.
- Workers: at most 48 in aggregate. Suggested waves: (1) BIRD x3 T1 at 12 workers + HotpotQA G at 12; (2) ToolHop x3
  at 16; (3) HoVer x3 at 16; (4) GPQA x3 at 12 + remaining HotpotQA at 6 each; (5) AIME x2 + LiveBench x3 at 8;
  T2 / T3 / T4 fill free slots at 8 workers as their T1 runs finish. Wall time est. 6-9 h (TEST-A: BIRD 10 min,
  ToolHop 40 min, GPQA 25-30 min per cell).
- Reserve after TEST-B: 33 - 23.7 = about 9 USD (est.).

### 4.4 Order of work

1. User go-ahead for the downloads (BIRD `dev.json`; optionally AIME 2026 and a later LiveBench release).
2. Freeze commit on `main`: `frozen_decisions_11.json`, the rule text of section 2, `testb_v11.py`, the builder script,
   worker v92 hash; package: set the evaluated defaults (5.2).
3. Materialize `testb-eval-v1` for every benchmark; commit the manifest and the pre-registration (sections 3.2-3.7 as
   `docs/PREREG-TESTB-20261121.md` with all hashes); mirror to R2; ledger entry.
4. Run T1, then T2 / T3 / T4; relaunch rules of 3.6.
5. Run `testb_v11.py` once; publish `testb_result.json`, the three tables, and the per-item rows.

---------------------------------------------------------------------------------------------------------------------

## 5. Anything still worth doing before the freeze?

### 5.1 Paid candidates - verdict: freeze now

| candidate | est. gain | est. cost | verdict |
|---|---|---|---|
| ToolHop abstention-triggered retry | +1 .. +2 on ToolHop (mostly the GEPA cell), about +0.3 on the TEST-B core mean | 0.5-1 USD for P+F and DEV, a new worker version (v93), a new gate, half a day | no - small, unmeasured, and it delays the freeze; keep for 1.2 |
| IFBench checker (free replay) / retry | +1.5 .. +3 on IFBench | 0 / 1-2 USD | no - re-implements the grader, and IFBench has no clean test pool, so it could not be confirmed |
| PUPA detail-count selection / retry | +0.3 .. +1.2 mean (one cell) | 0 / 2-3 USD | no - PUPA is exhausted; judge noise is about 1 pp |
| verifier on DEV for the non-gated cells | information only | 1-2 USD | no - they are off by the frozen gate |
| more samples (GPQA) | negative in the replay | - | no |

The whole remaining budget is better spent on TEST-B itself (n on BIRD and HoVer).

### 5.2 Zero-cost items that belong to the freeze (do them, they are not experiments)

1. Write `frozen_decisions_11.json` from the draft and decide "ladder vs full everywhere" as the primary policy
   (section 2.2) - before the pre-registration.
2. Package = evaluated method: `doc_set` must use the fixed cap of the program's budget (24 on HoVer), not the
   program's count on the item; the per-task mode (lite / full / verifier) and the "verdict applies only if its base
   is the pick" rule must be expressible in the package configuration; the abstention checker is already identical
   (same regular expression).
3. Wording: the 1.1 verifier is deployed in 8 cells (11 passed the cell gate); LiveCodeBench's verifier and
   NATURAL PLAN stay development-only results in 1.1's evidence; ToolHop's filter is a declared checker with no
   measurable gain.

---------------------------------------------------------------------------------------------------------------------

## 6. Risks and what I did not verify

1. BIRD full dev: its size, the overlap rule with Mini-Dev and the difficulty mix are from memory; the file is not on
   the server. Its gold labels are noisier than Mini-Dev's corrected ones.
2. AIME 2026 and a later LiveBench release: existence and format not checked (no download was made).
3. Costs are estimates from per-item prices of other runs; GEPA-cell prices were rescaled (4.3). LiveCodeBench showed
   that fresh items can cost several times the development price.
4. The ladder rule was written today, with the project's DEV history known; it uses P+F only, but its form (1 se,
   pooled per benchmark) is my choice. Two of its acceptances are exact ties (LiveBench, NATURAL PLAN).
5. Power numbers use DEV standard deviations; BIRD on the noisier full dev may have a different variance.
6. Whether `test_node.py`'s contract edits work unchanged for HoVer / HotpotQA / AIME / LiveBench contracts (they
   never had a test dir) was read from the code, not executed.
7. The hover_control numbers are quoted from the task brief; the script was read, its log was not found on the server.

## 7. Files

- Server (read): `/root/pt-export/table11.py` (sha256 f20b9405...bb9d), `table11_final.json` (9efca149...44c0) and
  `.log`, `s2_gate_pf.log`, `s2_gate_dev.log`, `bird_exec.json`; `/root/s3_state.json`, `/root/s3b_state.json`;
  `verify-*.jsonl` and `worker-summary.json` of the S1 / S2 / S3 / TEST-A runs; `/root/rider-helpers/test_node.py`;
  `scripts/prepare_fieldsuite_{hover,hotpot,gpqa,pupa}_roles_v1.py`; manifests of `.external/fieldsuite-*-data-v1`,
  `fieldsuite-test-opened-v1/OPENED.json`, `newdata-src-v1/bird/data/manifest.json`. Repo HEAD 3159ec1a, clean.
- Server (written, helpers only): `/root/fable-freeze/{audit11.py, sum11.py, ladder.py, pools.py, costs.py, c5.py,
  audit_rows.json, audit_cells.json, ladder.json, audit11.py.log}`.
- Local: `scratchpad\server\*.py`, `scratchpad\gh_pt\research\{rule,analysis,results}`, `scratchpad\gh_pt\src\tribes`,
  the three earlier Fable reports; outputs in `scratchpad\fable\freeze\`.
