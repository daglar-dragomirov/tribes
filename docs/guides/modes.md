# Choosing a mode

| | `lite` | `full` |
|---|---|---|
| runs per input | reviewer (whose draft is one program run) | program + reviewer; agent only on disagreement |
| inference cost | about 2.6× the program | about 4.6× the program |
| development gain, 1.1 (36 cells, post hoc) | +10.1 pp | +11.8 pp (with the verifier) |
| development gain, 1.0 (36 cells, post hoc) | +8.9 pp | +9.5 pp |
| sealed-test gain (15 cells) | +7.1 pp | not measured |

The cost multiples are for 1.1 (the agents on the task model). With `agent_lm` at a higher reasoning effort (1.2) the
agents' calls are longer and cost more; the program's calls do not change.

On fresh items (TEST-B, 15 cells, TRIBES 1.1) `full` beat `lite` by +2.0 pp [+1.2, +2.7] on the same forms. The
per-task choice of mode (fixed on selection data) gained +4.7 pp over the programs, and `full` everywhere plus the verifier
+5.2 pp.

Use **`lite`** when cost matters or outputs are free text (summaries, code, document sets), where two forms almost never
agree word for word and the vote has nothing to do.

Use **`full`** when answers are short and comparable (numbers, labels, option letters, SQL results): there the vote of
independent forms adds the most.

Either way, `fit` decides per task whether the layer is used at all. Where it is switched off, the cost is the program's.

## What the tests used (TRIBES 1.2)

| task type (benchmarks) | mode | agents' reasoning effort | agent steps · retry | extra |
|---|---|---|---|---|
| math (AIME, LiveBench) | `full` | high | 8 · no | — |
| multiple choice (GPQA) | `lite` | high | 8 · no | — |
| text-to-SQL (BIRD) | `lite` | high | 8 · no | agents get `run_sql` |
| planning (NATURAL PLAN) | `full` | high | 8 · no | the plan validator as checker |
| instruction following (IFBench) | `lite` | high | 8 · no | — |
| tool QA (ToolHop) | `full` | high | 16 · yes | an abstention is not an answer |
| retrieval sets (HoVer) | `full` | high | 16 · yes | `doc_set()` merge |
| code (LiveCodeBench) | `full` + verifier | task model | 8 · no | public tests as checker |
| multi-hop QA, privacy rewrite (HotpotQA, PUPA) | `lite` | task model | 8 · no | — |
| function calling, agents (BFCL, τ²-bench) | layer off | — | — | the switch keeps the program |

Every entry was decided on the optimizer's own selection data (PARETO + FIT) by a gate fixed in advance, before the
tests were opened; "high" means `agent_lm` set to the task model at reasoning effort high (max_tokens 32,768).
