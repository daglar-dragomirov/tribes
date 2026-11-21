"""Shared fakes: forms are plain callables, so the selection logic is tested without any model call."""
from __future__ import annotations

import threading
from typing import Any, Callable

import dspy
import pytest

from tribes import Tribes


class FakeForm:
    """A form whose answer is a function of the inputs; records calls; can fail a given number of times."""

    def __init__(self, answer: Callable[[dict], Any] | Any, fail_times: int = 0, delay: float = 0.0,
                 barrier: threading.Barrier | None = None, extra: dict | None = None):
        self.answer = answer if callable(answer) else (lambda _inputs, a=answer: a)
        self.fail_times, self.delay, self.barrier, self.extra = fail_times, delay, barrier, extra or {}
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, **inputs):
        with self._lock:
            self.calls += 1
            n = self.calls
        if self.barrier is not None:
            self.barrier.wait(timeout=5)
        if self.delay:
            import time
            time.sleep(self.delay)
        if n <= self.fail_times:
            raise ValueError("unparseable output")
        a = self.answer(inputs)
        if isinstance(a, Exception):
            raise a
        return dspy.Prediction(answer=a, reasoning=f"because {a}", **self.extra)


@pytest.fixture
def program():
    return dspy.Predict("question -> answer")


@pytest.fixture
def make_pt(program):
    def make(rigid, assembled, liquid, **kw):
        forms = {"rigid": rigid if isinstance(rigid, FakeForm) else FakeForm(rigid),
                 "assembled": assembled if isinstance(assembled, FakeForm) else FakeForm(assembled),
                 "liquid": liquid if isinstance(liquid, FakeForm) else FakeForm(liquid)}
        kw.setdefault("retries", 0)
        return Tribes(program, forms=forms, **kw)
    return make


def exact(ex, pred, trace=None):
    return float(str(pred.answer).strip() == str(ex.answer).strip())


def examples(pairs):
    return [dspy.Example(question=q, answer=a).with_inputs("question") for q, a in pairs]
