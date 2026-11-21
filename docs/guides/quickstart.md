# Quick start

## Install

```bash
pip install tribes
```

TRIBES needs Python 3.10+ and DSPy 3. It works with any language model DSPy supports.

## 1. Get a program

Use the program your optimizer returned, or any `dspy.Module`:

```python
import dspy

dspy.configure(lm=dspy.LM("openrouter/z-ai/glm-5.3-flash"))
program = dspy.GEPA(metric=metric, auto="medium").compile(student, trainset=train, valset=val)
```

## 2. Wrap it

```python
from tribes import Tribes

pt = Tribes(program, mode="full", examples=train)
```

`examples` are a few labeled items whose correct outputs are shown to the agents, so they follow the expected format.
Input and output fields are read from the program; pass `input_fields` / `output_field` if it has several outputs.

## 3. Decide once per task

```python
pt.fit(train + val, metric, num_threads=8)
print(pt.report["use_layer"], pt.report["mean_gain"], pt.report["se"])
```

`fit` runs the three forms on labeled data and checks that TRIBES is not worse than the program by more than one
standard error. The data the optimizer already saw is fine here. If the answer is no, `pt` behaves exactly like the
program.

## 4. Use it

```python
prediction = pt(question="What is 2**10 + 24?")
print(prediction.answer)
```

The call signature is the program's. The returned object is the prediction of the chosen form.

!!! tip "Make it stronger on your task"
    If answers can be compared better than as plain text (numbers, option letters, SQL result sets), pass an
    `answer_key`. If there is a cheap check that needs no labels (public unit tests, "the query runs"), pass a `checker`.
    See [Answer keys and checkers](keys-and-checkers.md).
