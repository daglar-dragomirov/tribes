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
    About 2.6× the program's inference cost in `lite` mode and 4.6× in `full` mode; nothing at optimization time. `fit`
    runs the forms once on your selection data.

??? question "Why is the test gain lower than the development gain?"
    The 1.0 rule was designed after the development outputs were seen. The sealed test, opened once after everything was
    frozen, is the honest number: +7.1 pp on 15 cells. TRIBES 1.1 was then confirmed on 1,010 fresh items
    (TEST-B, pre-registered): +4.7 pp over the programs. See the [results](../results.md).
