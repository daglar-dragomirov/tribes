# How it works

TRIBES never changes the optimized program. It adds two forms around it and a rule that picks one output.

## The three forms

| form | what it is |
|---|---|
| **rigid** | the optimized program, unchanged |
| **assembled** | the program writes a draft; a ReAct reviewer checks it against the task and fixes it only if it finds a concrete defect |
| **liquid** | a ReAct agent that solves the task from scratch |

Both agents share one instruction head: the program's own predictor instructions (the task's purpose plus what the
optimizer learned), optionally a few correct outputs of labeled examples, and one fixed template per form. The reviewer is
told to keep the draft unless it can confirm a defect, and never to replace it with "cannot be determined". Both agents
have `run_python` (a 10-second Python subprocess) and the task tools you pass.

## Agents that think longer (1.2)

Since 1.2 the layer's own agents can run on their own LM (`agent_lm`): typically the same model at a higher reasoning
effort, while the program and the program's draft inside the reviewer keep your task LM. On tool tasks the agents also
get more steps (`max_iters=16`) and one fresh run when they return nothing or abstain (`agent_retry=True`).

On the pre-registered TEST-C this took the layer from +11.5 to **+14.3 pp** over the programs on the same items. Running
the *program* at the same high effort instead gains only +7.9: on HoVer, ToolHop and BIRD almost nothing (under two
points), so the gain there is the layer, not the extra thinking. On GPQA and IFBench the program at high effort alone
does better than the layer; there the extra thinking is what helps.

## Set-valued outputs: merge instead of select

When the output is a set scored by recall (retrieved documents, cited sources), `tribes.tasks.doc_set()` makes the
layer merge rather than pick: an element-wise vote over the three forms' sets, capped at the program's own output size.
On HoVer it beat merging three samples of the program by +7.1 pp (TEST-B); the whole layer gains +20.3 pp there on
TEST-C.

## Contested inputs: the verifier

When no two forms agree, an optional verifier (`verifier=True`) settles the input by evidence: it designs and runs one
check whose outcome differs between the candidates, and code, not the model, accepts a switch only if the quoted
evidence matches a tool observation. A switch needs two of three votes. `fit` turns it on per task only if it wins
clearly more items than it loses. 1.2 drops it on math, where it had been chosen with the agents at low effort; it
stays on for code.

## Settings per task type

These are the settings the tests used:

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

## One answer per input

1. **Drop broken outputs.** A form whose output is missing or cannot be parsed is out.
2. **Task check.** If you pass a `checker`, forms whose output fails it are out (if all fail, all stay).
3. **Vote.** If two surviving forms give the same answer under `answer_key`, that answer is returned.
4. **Reviewer.** Otherwise the reviewer's answer, then the program's, then the agent's.

The vote needs two *independent* opinions: the program's own output comes from a separate call, not from the reviewer's
draft. In `full` mode the agent runs only when the program and the reviewer disagree.

## Never worse than the program

`fit` compares TRIBES with the program item by item on labeled selection data. Let *d* be the mean difference and
*se* its standard error (clustered when items repeat). The layer is used only if

**d + 1.0 × se ≥ 0**

otherwise the wrapped object is the program alone. The burden of proof is on harm, not on benefit: the program scores
optimistically on data the optimizer saw, so demanding a significant gain there would switch off the layer where it
helps.
