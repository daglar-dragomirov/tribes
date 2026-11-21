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
