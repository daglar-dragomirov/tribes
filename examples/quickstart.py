"""TRIBES quickstart: wrap an (optimized) DSPy program, decide on labeled data, then answer.

Run:  OPENROUTER_API_KEY=... python examples/quickstart.py
Any LM that DSPy supports works; the model below is only an example.
"""
import os

import dspy

from tribes import TRIBES

lm = dspy.LM(os.environ.get("PEACHTREES_MODEL", "openrouter/z-ai/glm-5.3-flash"), max_tokens=4096)
dspy.configure(lm=lm)

# 1. Your program. In practice: the program returned by dspy.GEPA / MIPROv2 / SIMBA .compile(...).
program = dspy.ChainOfThought("question -> answer")

# 2. Labeled selection data (the optimizer's train / val sets are fine) and the task metric.
data = [
    ("A shop sells pens at 3 for $2. How many dollars do 12 pens cost?", "8"),
    ("What is 17 * 23?", "391"),
    ("How many prime numbers are there below 30?", "10"),
    ("A train travels 180 km in 2.5 hours. What is its average speed in km/h?", "72"),
    ("What is the sum of the digits of 2**15?", "26"),
    ("How many days are there in a leap year?", "366"),
]
selection = [dspy.Example(question=q, answer=a).with_inputs("question") for q, a in data]


def metric(example, pred, trace=None):
    return float(str(pred.answer).strip().rstrip(".") == example.answer)


# 3. Wrap, decide once per task, use.
pt = Tribes(program, mode="lite", examples=selection)
pt.fit(selection, metric, num_threads=4)
print({k: v for k, v in pt.report.items() if k != "items"})
print(pt(question="What is 2**10 + 24?").answer)
