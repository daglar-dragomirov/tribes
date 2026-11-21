# TRIBES 1.1 — pre-registration of the confirmatory test TEST-B (2026-11-21)

Committed to `main` before any model has seen a TEST-B item. Design: Fable 5.2, `FABLE-FREEZE-TESTB-20261120` (audit,
freeze, TEST-B), adopted with the changes listed in section 8. TEST-A (TRIBES 1.0-lite on the sealed TEST, +7.1 pp over
15 cells, 2026-11-20) stays the 1.0 result; TEST-B is a separate test on fresh items and the two are never pooled.

## 1. What is frozen

- **Method**: TRIBES 1.1 = the frozen ladder policy in `docs/tribes-11/frozen_decisions_11.json` (every decision from
  PARETO + FIT only): forms rigid (the optimizer's program), assembled (the program's draft + a ReAct reviewer), liquid
  (a ReAct agent); liveness and task checker first; per benchmark **lite** (BIRD with run_sql agents, GPQA, HotpotQA),
  **full** (HoVer = element-wise set merge, cap 24; ToolHop = vote + abstention checker); the do-no-harm switch
  (z = 1, PARETO + FIT) is on in all 15 cells. The verifier is deployed in none of the 15 cells (its benchmark-level rung
  was rejected for BIRD, GPQA and HotpotQA).
- **Secondary policy "1.1-full"** (the development table's policy): full everywhere + the verifier in BIRD-GEPA,
  GPQA-SIMBA, HotpotQA-SIMBA (the core cells whose verifier cell gate passed).
- **Code**: worker `src/rider4d/fieldsuite_worker_v92.py` (sha256 d8decbd5…c6aa; LF form e9f28517…603e), item rule
  `src/rider4d/peachtrees_v1.py` (ee450df5…3a9a), node builder `scripts/tribes_testb_node.py`, analysis
  `scripts/tribes_testb_v11.py`, item builder `scripts/prepare_testb_v1.py` (bf5ba877…2e85). Model: `z-ai/glm-5.3-flash`
  via open-inference in every arm, as in development.

## 2. Items (fresh; disjoint from every role, the sealed TEST and the v0.2-opened sets)

Seed 20261120 for every draw. Files: `.external/fieldsuite-<ds>-data-v1/testb-eval-v1/` (DEV.jsonl = the TEST-B items;
FIT / PARETO = byte copies of roles-v1).

| benchmark | n | pool | TEST-B DEV.jsonl sha256 |
|---|---|---|---|
| BIRD | 300 | BIRD dev (dev_20240627) minus the 500 Mini-Dev-2024 ids, minus 93 near-duplicates of Mini-Dev-1024 items (token similarity >= 0.40), gold runs on the original dev databases in < 30 s with rows (942 of 942); every challenging (34) and moderate (182) item + 84 simple by sample | 947033aac1a4d1480f0fd4f55dc89a9b9ae69b4ed9f00eff4de46e85ff4b37e7 |
| ToolHop | 200 | 495 unused of 995 | d9c149f5c90f2f3ff1b01b9ddbfb623f830fb9775477df1c7b2bf8545bf92b50 |
| GPQA | 160 | all of GPQA-main minus Diamond minus FIT / PARETO | 9d355b0a518442b9fe0d4cb52ae5becf9f5bcb48152fbe79bc0069c98c8e6481 |
| HoVer | 150 | the artifact's test pool (2,433) minus the 300 sealed / opened ids | 3d45efaad6f89beb939f0052e806b1b054a95e3df4c41e011d758cf5ad3a4344 |
| HotpotQA | 200 | the artifact's test pool (36,178) minus the 300 sealed / opened ids | debb4ba9db9dd45dfa8fa2f89ac5a5d08c494b14c23507385400ede7e0862888 |

BIRD runs on the original dev databases (`newdata-src-v1/bird/dev_20240627/dev_databases`; the Mini-Dev databases are
trimmed copies on which dev gold queries return other rows). The schema text in the prompt is the roles' Mini-Dev text
(same tables and columns). Caveats stated in advance: the full-dev gold labels are noisier than the corrected Mini-Dev
ones, and TEST-B BIRD is easier than Mini-Dev-1024 (28 % simple items vs 2 %); absolute accuracies differ from
development for every arm.

## 3. Cells and runs

15 cells = {BIRD, ToolHop, GPQA, HoVer, HotpotQA} x {GEPA, MIPROv2, SIMBA}; each node is a child of the cell's
development node with that cell's own contract (roles -> testb-eval-v1), forms only, parse retry 3, launched with the
supported launcher after the full live preflight. Output names `fieldsuite-v04-x1<cell>` (T1), `x2<cell>`, `x4<cell>`.

| node | what | cells |
|---|---|---|
| T1 | rigid, liquid, assembled on TEST-B (BIRD: agents with run_sql; HoVer: + rigid2, rigid3 = the program x 3 control) | 15 |
| T2 | BIRD: the 1.0 agents (no run_sql) re-run; the program's rows replayed from T1 | 3 |
| T4 | the verifier v2 replayed over T1's forms (for the 1.1-full secondary arm only) | ptbr, ptsg, ptsh |

Concurrency: at most 48 workers in aggregate (12 per T1 node, 8 per T2 / T4). Money: expected about 17 USD; per-node
`max_usd` caps; nothing is launched if the account would keep less than 2 USD after the live runs' estimates.

## 4. Endpoints (fixed order)

Item scores are the worker's own (BIRD: execution match; ToolHop / GPQA / HotpotQA: exact match; HoVer: all three gold
documents among the retrieved titles). Arms per item: program; 1.0-lite (assembled, the program if assembled has no
usable output; BIRD: the 1.0 reviewer); 1.0-full (the 1.0 vote over the three 1.0 forms); **1.1**; 1.1-full.

- **Primary (one)**: the unweighted mean over the 15 cells of the cell mean of score(1.1) − score(program). One-sided
  test of "> 0" at α = 0.025: the claim holds iff the lower end of the 95 % percentile interval is > 0. Bootstrap:
  10,000 draws, seed 11, items resampled with replacement within each benchmark (one draw serves the benchmark's three
  cells).
- **Secondary, fixed sequence** (tested only while every earlier claim holds, same test): S1 1.1 − 1.0-lite, all
  cells; S2 BIRD cells: 1.1 − 1.0-lite; S3a HoVer cells: merge − reviewer; S3b HoVer cells: merge − program x 3 merged
  (the same vote and cap over three program samples).
- **Per benchmark**: 1.1 − program over its three cells, one-sided bootstrap p, Holm over the five benchmarks at 0.025.
- **Descriptive, not tested**: 1.1 − 1.1-full; 1.0-full − 1.0-lite; 1.0-lite − program on these items; 1.1-full −
  program; full − lite; the agent alone − program; BIRD gains by difficulty; per-cell tables; dead rows per form;
  costs from `worker-summary.json`.
- **Expected values** (Fable's estimates, 0.64 x DEV): primary **+6.1 pp** (range +4.5 .. +8); S1 **+2.6 pp**; BIRD
  +14.8, HoVer +8.0, ToolHop +3.0, GPQA +2.3, HotpotQA +2.1. Reading fixed now: a primary result between +4 and +8 with
  BIRD and HoVer clearly positive confirms 1.1; a result near 1.0-lite on the same items means the new components did not
  transfer. ToolHop, GPQA and HotpotQA are not expected to be significant on their own at these n.

## 5. Exclusions and failures (fixed in advance)

- No item is excluded after this commit. A form without usable output is handled by the rule itself; if the returned
  form has no output, the item scores 0 for that arm.
- A run that stops early (budget, crash, provider outage) is relaunched as the same frozen node with the supported
  launcher; the analysis reads the newest complete run of each node. A cell is missing only after two failed
  relaunches; it is reported and leaves the mean (stated), never replaced.
- Transport errors are repaired once, identically for every arm, decided from error counts alone before any score is
  read. Parse failures are not repaired beyond parse retry 3.
- `scripts/tribes_testb_v11.py` runs once, on complete data. If a defect is found afterwards, both versions are
  published.

## 6. The verifier: a separate confirmatory family (TEST-B2), not part of this primary endpoint

The verifier's deployed cells (AIME GEPA / SIMBA, LiveBench x 3) have no fresh pool on the server. If AIME 2026 and a
LiveBench release newer than the cached one are obtained (each download needs the user's go-ahead), their items are
materialized and hashed in a separate pre-registration before any run; endpoint: full + verifier − full on those
cells. Without them the verifier stays a development result (DEV: 50 switches won, 7 lost in the gated cells).

## 7. What would be reported whatever happens

All 15 cells with n, program, every arm, gain and interval; the primary and every secondary in the order above, with
"not tested" where the sequence stopped; missing cells; costs. TEST-A, TEST-B and the development table stay three
separate tables.

## Amendment 1 (2026-11-20 23:55 MSK; before any score was read, analysis not run)

The first four T1 runs used 48 workers; the HotpotQA-GEPA run lost rows to HTTP 429 rate limits (assembled 81,
liquid 20, rigid 23 of 200; the three BIRD runs lost none). Section 5's transport repair is implemented as a TR node
(`tribes_testb_node.py TR`, worker v92's `repair_transport_errors`: the run's saved rows replayed, only transport-failed
rows evaluated again, every form, until they go through), queued automatically for any T1 / T2 run with transport-failed
rows, decided from the error counts alone. The analysis reads the TR run (`xr1<cell>`, `xr2<cell>`) when complete, else
the node's own run; T4 replays the repaired forms. Aggregate concurrency is lowered from 48 to 36 workers. Nothing
else changes.

## Amendment 2 (2026-11-21 02:55 MSK; all 23 nodes finished, analysis not run)

The TR runs (`xr1j6h`: 124 rows, `xr1j6v`: 3 rows; every row went through on the first pass) write only the re-evaluated
rows (`eval-selu-repair<k>-DEV-<form>.jsonl`), not whole form files, so Amendment 1's "read the TR run when complete"
never matched. The analysis now lays those rows over the node's own saved rows by uid (later passes last), for T1 and T2,
and reports the counts. While checking completeness before the analysis, the three T4 runs' worker summaries were
displayed (verifier switches: BIRD-GEPA 1 won / 1 lost, GPQA-SIMBA none, HotpotQA-SIMBA 1 won / 0 lost); they feed only the
descriptive 1.1-full arm and change nothing here.

## 8. Changes against Fable's TEST-B design

1. The primary policy is the ladder (Fable's recommendation); 1.1-full is the nested secondary.
2. The extension tier (AIME 2026, later LiveBench) is not in this primary endpoint; it becomes the separate family of
   section 6 (its sources are not on the server).
3. BIRD: the original dev databases (Fable assumed the Mini-Dev ones are the same; they are trimmed copies).
   Near-duplicates of the Mini-Dev-1024 items are removed by a fixed similarity cutoff; the difficulty rule is "every
   challenging and moderate item first" (the closest the pool allows to Mini-Dev's mix).
4. HoVer's program x 3 control runs inside T1 (forms rigid2, rigid3) instead of a separate node.
5. The verifier secondary (T4) also covers GPQA-SIMBA, whose cell gate passed as well.
