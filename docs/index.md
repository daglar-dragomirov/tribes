---
hide:
  - navigation
  - toc
---

<h1 class="tb-sr">TRIBES</h1>

<div class="tb-hero" markdown>

![TRIBES](assets/lockup-light.png#only-light){ .tb-lockup }
![TRIBES](assets/lockup-dark.png#only-dark){ .tb-lockup }

<p class="tb-tagline">Inference-time answer selection for optimized DSPy programs</p>

[Get started](guides/quickstart.md){ .md-button .md-button--primary }
[Results](results.md){ .md-button }
[GitHub](https://github.com/daglar-dragomirov/tribes){ .md-button }

</div>

<div class="tb-stats" markdown>
<div class="tb-stat"><b>+43 pp</b><span>up to · AIME 2026</span></div>
<div class="tb-stat"><b>−50 %</b><span>errors</span></div>
<div class="tb-stat"><b>87.3 %</b><span>GEPA + TRIBES · GEPA 70.9 %</span></div>
<div class="tb-stat"><b>0</b><span>extra optimization cost</span></div>
</div>

TRIBES is an inference-time layer for optimized DSPy programs. It keeps the program a prompt optimizer produced,
adds a reviewer of its draft and an independent agent, picks one answer per input with a label-free rule, and switches
itself off on any task where it is not at least as good as the program.


=== "GEPA"

    ![GEPA vs GEPA + TRIBES](assets/chart-testc-gepa-light.png#only-light)
    ![GEPA vs GEPA + TRIBES](assets/chart-testc-gepa-dark.png#only-dark)

=== "MIPROv2"

    ![MIPROv2 vs MIPROv2 + TRIBES](assets/chart-testc-mipro-light.png#only-light)
    ![MIPROv2 vs MIPROv2 + TRIBES](assets/chart-testc-mipro-dark.png#only-dark)

=== "SIMBA"

    ![SIMBA vs SIMBA + TRIBES](assets/chart-testc-simba-light.png#only-light)
    ![SIMBA vs SIMBA + TRIBES](assets/chart-testc-simba-dark.png#only-dark)

=== "Mean of the three"

    ![program vs program + TRIBES](assets/chart-testc-light.png#only-light)
    ![program vs program + TRIBES](assets/chart-testc-dark.png#only-dark)

=== "13 benchmarks (development)"

    ![development, 13 benchmarks](assets/chart-dev-light.png#only-light)
    ![development, 13 benchmarks](assets/chart-dev-dark.png#only-dark)

## Get started

```bash
pip install tribes
```

=== "GEPA"

    ```python
    import dspy
    from tribes import Tribes

    dspy.configure(lm=dspy.LM("openrouter/z-ai/glm-5.3-flash"))
    program = dspy.GEPA(metric=metric, auto="medium").compile(student, trainset=train, valset=val)

    pt = Tribes(program, examples=train).fit(train + val, metric)
    print(pt(question="...").answer)
    ```

=== "MIPROv2"

    ```python
    program = dspy.MIPROv2(metric=metric, auto="heavy").compile(student, trainset=train)

    pt = Tribes(program, examples=train).fit(train + val, metric)
    ```

=== "SIMBA"

    ```python
    program = dspy.SIMBA(metric=metric).compile(student, trainset=train)

    pt = Tribes(program, examples=train).fit(train + val, metric)
    ```

=== "Any DSPy program"

    ```python
    program = dspy.ChainOfThought("question -> answer")

    pt = Tribes(program, mode="lite").fit(labeled, metric)
    ```

## How it works

<div class="grid cards" markdown>

-   :material-source-branch:{ .lg } **Three forms**

    ---

    The optimized program, a ReAct reviewer of its draft, and an independent ReAct agent that can think longer than
    the program. No task-specific prompt text.

    [:octicons-arrow-right-24: How it works](guides/how-it-works.md)

-   :material-vote:{ .lg } **One answer per input**

    ---

    Drop broken outputs, run a cheap task check if you have one, take the answer two forms agree on, else the
    reviewer's.

    [:octicons-arrow-right-24: Answer keys and checkers](guides/keys-and-checkers.md)

-   :material-shield-check:{ .lg } **Never worse**

    ---

    Once per task, a non-inferiority test on labeled data decides whether the layer is used at all.

    [:octicons-arrow-right-24: Choosing a mode](guides/modes.md)

-   :material-chart-bar:{ .lg } **Measured**

    ---

    36 development cells, a sealed test opened once and two pre-registered tests on fresh items, every number per cell.

    [:octicons-arrow-right-24: Results](results.md)

</div>

## Citation

```bibtex
@software{dragomirov2026tribes,
  author = {Dragomirov, Daglar},
  title  = {TRIBES: Inference-time answer selection for optimized DSPy programs},
  year   = {2026},
  url    = {https://github.com/daglar-dragomirov/tribes}
}
```
