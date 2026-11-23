# TRIBES 1.2 — pre-registration of the confirmatory test TEST-C (2026-11-23)

Committed to `main` before any model has seen a TEST-C item. Plan: Fable 5.2, `FABLE-V12-PLAN-20261122` (diagnosis of
TEST-B, candidates, TEST-C), adopted with the changes in section 8. TEST-A (1.0-lite, +7.1 pp), TEST-B (1.1, +4.73 pp)
and TEST-C are separate tests and are never pooled. TEST-B is development data for 1.2 from 2026-11-22 on.

## 1. What is frozen

- **Method**: TRIBES 1.2 = `docs/tribes-12/frozen_decisions_12.json` (sha256 18b277af…0d0c): TRIBES 1.1 unchanged
  (forms, item rule, ladder modes, HoVer set merge cap 24, ToolHop abstention checker, BIRD run_sql agents, the
  do-no-harm switch decisions of 1.1) plus the components that passed their pre-fixed gate on PARETO + FIT (stratified
  screens, pooled weighted mean > 0 and >= 1 se, `docs/tribes-12/screens/`):
  - N1, the layer's own agents (agent and reviewer) at reasoning effort high, max_tokens 32,768 — the program and the
    reviewer's draft keep the task model: AIME, LiveBench, GPQA, BIRD, NATURAL PLAN, IFBench (and inside N12);
  - N12 = N1 + step limit 16 + one fresh run on an empty or abstained output: ToolHop, HoVer;
  - AIME and LiveBench drop the verifier (gated on effort-low forms); HotpotQA, PUPA, LiveCodeBench, BFCL and τ² are
    unchanged from 1.1; C4 (agent with demonstrations) is not adopted.
- **Code**: worker `src/rider4d/fieldsuite_worker_v95.py` (LF sha256 9de9bb95…9baf), item rule
  `src/rider4d/peachtrees_v1.py` (unchanged), node builder `scripts/tribes_testc_node.py`, analysis
  `scripts/tribes_testc_v12.py`, item builder `scripts/prepare_testc_v1.py`. Model: `z-ai/glm-5.3-flash` via
  open-inference in every arm.

## 2. Items (fresh; disjoint from every role, the sealed TEST-A, the v0.2-opened sets and TEST-B)

Seed 20261123. Economy design: where the pool allows, every optimizer gets its own third of the items (the cells of a
benchmark do not share items); AIME 2026 is shared by its three cells.

| benchmark | n (gepa / mipro / simba) | pool | DEV sha256 (gepa / mipro / simba) |
|---|---|---|---|
| ToolHop | 99 / 98 / 98 | all 295 left of 995 | 07b80016… / 1507409f… / 8e5d27ed… |
| HoVer | 100 / 100 / 100 | 300 of the 1,983 left in the artifact's test pool | d3671e99… / db6f8dc1… / 6013f8fc… |
| NATURAL PLAN | 50 / 50 / 50 (25 trip + 25 meeting each) | trip + meeting minus roles and TEST-A | 65f55c1d… / 9bddc10a… / 9c6829b2… |
| IFBench | 50 / 50 / 50 | IFBench_train rows >= 600 in no role (served as role_indices) | indices 55e7229e… / 5afbe4a2… / 5953f0f9… |
| BIRD (simple only) | 100 / 100 / 100 | BIRD dev simple items left after TEST-B; uncorrected gold | 83091830… / 4d76219c… / acceb623… |
| GPQA-extended | 33 / 33 / 32 | GPQA-extended minus GPQA-main (98; keys of lower quality) | 6e863977… / 0cf7a4f7… / aba1ef8b… |
| AIME 2026 | 30, shared | MathArena/aime_2026, one sample per problem (downloaded 2026-11-22) | 6f38b13a… |

Full hashes are in each `testc-eval-v1*/manifest.json` (and `fieldsuite-ifbench-data-v1/testc-v1/manifest.json`).
Not in TEST-C: LiveBench (no release newer than the cached one), LiveCodeBench (no fresh items), HotpotQA and PUPA
(unchanged in 1.2), BFCL (layer off), τ² (ceiling).

## 3. Cells and runs

21 cells = 7 benchmarks × {GEPA, MIPROv2, SIMBA}; each node is a child of the cell's development node with that cell's
own contract (roles → the cell's TEST-C items served as DEV), forms only, parse retry 3, launched with the supported
launcher after the full live preflight. One T1 node per cell (output `fieldsuite-v04-c1<cell>`):
forms `rigid` (the program), `liquid`, `assembled` (1.1), `liquid_v12`, `assembled_v12` (1.2), `rigid_hi` (the program at
effort high: the compute-matched control). A T1 run with transport-failed rows gets one TR node (`cr1<cell>`), decided
from the error counts alone; the analysis lays its rows over the T1 rows by uid. At most 36 workers in aggregate (12 per
node). Expected cost: about 32 USD (+8 % retries); per-node `max_usd` caps; the runner waits when the account would keep
less than 2 USD after the live runs' estimates.

## 4. Endpoints (fixed order)

Item scores are the worker's own (ToolHop, GPQA, AIME: exact match; HoVer: all three gold documents among the retrieved
titles; BIRD: execution match on the dev databases; NATURAL PLAN: the official validators; IFBench: the instruction
checker). Arms per item: prog; v11 (the 1.1 rule over rigid / liquid / assembled, 1.1 mode and switch, no verifier);
**v12** (the same rule over rigid / liquid_v12 / assembled_v12, 1.2 mode and switch); ctrl (rigid_hi).

- **Primary (one)**: the unweighted mean over the 21 cells of the cell mean of score(v12) − score(prog). One-sided test
  of "> 0" at α = 0.025: the claim holds iff the lower end of the 95 % percentile interval is > 0. Bootstrap 10,000
  draws, seed 23; items drawn with replacement within each cell (split benchmarks) or within the benchmark (AIME 2026).
- **Secondary, fixed sequence** (each tested only while every earlier claim holds): S1 v12 − v11, all cells (1.2 better
  than 1.1); S2 v12 − ctrl, all cells (better than the program given the same reasoning effort); S3 ToolHop v12 − v11;
  S4 HoVer v12 − v11.
- **Per benchmark**: v12 − prog over its three cells, one-sided bootstrap p, Holm over the seven benchmarks at 0.025.
- **Descriptive, not tested**: v11 − prog; ctrl − prog; the 1.2 agent and reviewer alone − prog; per-cell tables; dead
  rows per form; costs from `worker-summary.json`.

## 5. Expected values (estimates)

Screen increments (1.2 − 1.1 on PARETO + FIT) were selected by their gate on the same data, so they are shrunk by 0.5;
1.1 − program is taken from TEST-B where the benchmark was there.

| benchmark | 1.1 − program (source) | 1.2 − 1.1 (screen × 0.5) | expected 1.2 − program |
|---|---|---|---|
| HoVer | +12.4 (TEST-B) | +3.1 | +15 |
| ToolHop | +2.2 (TEST-B) | +3.8 | +6 |
| BIRD simple | +2.4 (TEST-B simple stratum) | +3 (simple items gain less) | +5 |
| GPQA-extended | +1.7 (TEST-B) | +2.2 | +4 |
| AIME 2026 | unknown on fresh items (DEV +31 with the verifier) | +2.8 | +10 .. +20, wide (n = 30) |
| NATURAL PLAN | +13.7 (TEST-A, 1.0-lite) | +0.8 | +14 |
| IFBench | +1.6 (DEV) | +1.1 | +3 |
| **primary, 21 cells** | | | **about +8 .. +10** |

Reading fixed now: a primary result clearly above TEST-B's +4.7 with S1 holding confirms that 1.2 improves on 1.1; S2
failing would mean the gain is mostly the extra reasoning effort, not the layer. GPQA-extended, IFBench and AIME 2026 are
not expected to be significant on their own at these n.

## 6. Exclusions and failures (fixed in advance)

Exactly section 5 of the TEST-B pre-registration: no item is excluded after this commit; a form without usable output is
handled by the rule (if the returned form has none, the item scores 0 for that arm); a run that stops early is relaunched
as the same frozen node (a cell is missing only after two failed relaunches, reported, never replaced); transport errors
are repaired once, identically for every form, decided from error counts alone; parse failures are not repaired beyond
parse retry 3. `scripts/tribes_testc_v12.py` runs once, on complete data; a defect found afterwards is reported with both
versions.

## 7. What would be reported whatever happens

All 21 cells with n, every arm, gain and interval; the primary and every secondary in order, with "not tested" where the
sequence stopped; missing cells; costs. TEST-A, TEST-B and TEST-C stay three separate tables.

## 8. Changes against Fable's TEST-C design

1. Items are split per optimizer where the pool allows (the user's cost limit); AIME 2026 is shared.
2. HotpotQA is not in TEST-C: no component passed there, so 1.2 = 1.1 on it.
3. The 1.1 arm on TEST-C runs without the verifier on AIME (1.2 drops it); the verifier family is not tested here.
4. LiveBench and LiveCodeBench have no fresh items; their 1.2 settings rest on development evidence only.
5. The compute-matched control (the program at effort high) runs on every item of every cell.
