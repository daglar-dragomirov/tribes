# FAQ

??? question "Does it need a judge model?"
    No. An earlier version used an LLM judge with a calibrated threshold. It added +0.8 pp for most of the cost and was
    removed: agreement between independent forms and cheap deterministic checks do the job better.

??? question "Which optimizers does it support?"
    Anything that produces a DSPy program. It was evaluated on GEPA, MIPROv2 and SIMBA, and it works on hand-written
    modules too.

??? question "What if it does not help my task?"
    Then `fit` reports `use_layer = False` and the wrapped object is the program, at the program's cost.

??? question "Is `run_python` a sandbox?"
    No. It runs the agent's code in a Python subprocess with a 10-second limit. Run untrusted workloads in an isolated
    environment (container, VM, no credentials in the environment).

??? question "How much does it cost?"
    About 2.6× the program's inference cost in `lite` mode and 4.6× in `full` mode with the agents on the task model
    (1.1); with `agent_lm` at a higher reasoning effort (1.2) the agents cost more. Nothing at optimization time. `fit`
    runs the forms once on your selection data.

??? question "Which numbers should I quote?"
    The tests, never the development table. Each version was frozen before its test was opened: 1.0 on the sealed test
    (+7.1 pp, 15 cells), 1.1 on TEST-B (+4.7 pp, 1,010 fresh items) and 1.2 on TEST-C (**+14.3 pp**, 1,323 fresh items,
    21 cells). They are different items and benchmarks, so they are reported side by side, never pooled. See the
    [results](../results.md).

??? question "Is the 1.2 gain just more reasoning effort?"
    No. TEST-C also ran the program itself at the same high effort: it gains +7.9 pp, against +14.3 for 1.2, and 1.2
    beats it by +6.4 pp [+4.3, +8.5]. On HoVer, ToolHop and BIRD the extra effort alone adds under two points. The
    exception is GPQA and IFBench, where the program at high effort alone does better than the layer.

??? question "Why was a test gain once lower than the development gain?"
    The 1.0 rule was designed after the development outputs were seen, so development overstated it (+9.5 against +7.1
    on the sealed test). TEST-C is higher than the 1.1 development table because 1.2 adds agents that think longer.
