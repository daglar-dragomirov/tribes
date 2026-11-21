# Research record

How the 1.0 rule was found, frozen and tested, and how 1.1 was confirmed on fresh items. The files are in
[`research/`](https://github.com/daglar-dragomirov/tribes/tree/main/research) on GitHub.

| step | what happened |
|---|---|
| v0.2 | forms + an LLM judge with a calibrated threshold and a gate: +6.6 pp over the programs (36 cells, development) |
| offline analysis | a replay of every saved per-item output, with no model calls, found a simpler rule that beats the judge |
| 1.0 frozen | the rule as code, replayed independently: +9.47 pp on the saved outputs, +9.50 pp after re-running only the outputs that had failed to parse |
| decisions frozen | the per-task decision fixed on FIT + PARETO + DEV before the test was opened |
| sealed test | 15 cells opened once: +7.1 pp, 7 significantly above the program, none significantly below |
| FNXL | GEPA vs GEPA + TRIBES: macro-F1 0.376 → 0.437 |
| 1.1 development | the 1.1 components (BIRD agents with `run_sql`, HoVer set merge, ToolHop abstention check, the verifier, a per-task `lite` / `full` choice), every decision on selection data: **+11.6 pp** over the programs on 36 cells (post hoc; 1.0: +9.5) |
| TEST-B (1.1) | 1,010 fresh items, 15 cells, pre-registered: **+4.7 pp** [+3.4, +6.1] over the programs, +2.2 pp over 1.0-lite; HoVer, HotpotQA and BIRD significant on their own |

## Reproduce the development table

`research/results/rows-dev-cells.jsonl.gz` holds every development item of the 39 cells: the frozen rule's answer-key
hashes, the label-free checker results and the scores of the three forms (PARETO, FIT and DEV; no task text, no test
items). The package alone reproduces the table, with no model call:

```bash
tribes replay research/results/rows-dev-cells.jsonl.gz --protocol --mode both
```

The switch is decided on PARETO + FIT and the gain is reported once on DEV, per cell. A test in the suite checks every
cell against `p2_repaired.json`. Three cells (AIME over GEPA and SIMBA, LiveBench over the second GEPA run) moved after
their last parse-failure repair runs finished, which is why the 36-cell mean is +9.50 rather than the +9.41 first
reported; no task decision changed.

## Protocol

- **Splits.** FIT (the optimizer's train set), PARETO (its validation set), DEV (development), TEST (sealed). Rules and
  thresholds were chosen on FIT and PARETO; DEV was used to report; TEST was opened once per cell after freezing.
- **Statistics.** Paired per-item differences; 95 % bootstrap intervals clustered by problem where items repeat.
- **Failures.** An output that could not be parsed was re-run with step-level retries in every arm, the program included,
  before the final numbers.
- **Cost accounting.** Every model call is priced; TRIBES costs about 2.6× (lite) to 4.6× (full) the program.

## Why test is lower than development

The family of rules was designed after development outputs were seen. FIT ↔ PARETO cross-validation and a
leave-one-benchmark-out check protect the choice *within* the family, not the family itself. The largest drop is BIRD
over GEPA (+20.5 → +2.5), the cell with the strongest winner's curse in the analysis.
