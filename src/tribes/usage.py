"""Per-form accounting: calls, failures, wall time, tokens and dollars.

Tokens come from DSPy's own usage tracker (one nested tracker per form call, so the numbers also roll up into any
tracker the caller opened with ``dspy.settings.track_usage``). Dollars come from a price table you pass
(``{model: (usd_per_million_input, usd_per_million_output)}``) or, failing that, from LiteLLM's model prices; a model
priced by neither is reported as unpriced rather than free.
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

Prices = Mapping[str, "tuple[float, float]"]


def _tokens(entry: Mapping[str, Any]) -> tuple[int, int]:
    p = entry.get("prompt_tokens", entry.get("input_tokens", 0)) or 0
    c = entry.get("completion_tokens", entry.get("output_tokens", 0)) or 0
    return int(p), int(c)


def price(model: str, prompt_tokens: int, completion_tokens: int, prices: Prices | None = None) -> float | None:
    """Dollar cost of one usage entry, or None if the model has no known price."""
    if prices:
        for name in (model, model.split("/", 1)[-1]):
            if name in prices:
                pin, pout = prices[name]
                return (prompt_tokens * pin + completion_tokens * pout) / 1e6
    try:
        import litellm

        a, b = litellm.cost_per_token(model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return float(a) + float(b)
    except Exception:
        return None


@dataclass
class FormUsage:
    calls: int = 0
    failures: int = 0
    seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    unpriced_calls: int = 0
    models: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"calls": self.calls, "failures": self.failures, "seconds": round(self.seconds, 3),
                "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                "cost_usd": round(self.cost, 6), "unpriced_calls": self.unpriced_calls, "models": dict(self.models)}


class Ledger:
    """Thread-safe accumulation of :class:`FormUsage` per form (plus ``verifier``)."""

    def __init__(self, prices: Prices | None = None):
        self.prices = dict(prices or {})
        self._lock = threading.Lock()
        self._by: dict[str, FormUsage] = {}
        self.items = 0

    def reset(self) -> None:
        with self._lock:
            self._by.clear()
            self.items = 0

    def add(self, form: str, seconds: float, usage: Mapping[str, Mapping[str, Any]] | None, ok: bool) -> dict[str, Any]:
        """Record one call; returns the call's own numbers (tokens, cost) for callbacks."""
        p_all = c_all = 0
        cost: float | None = 0.0
        for model, entry in (usage or {}).items():
            p, c = _tokens(entry)
            p_all, c_all = p_all + p, c_all + c
            v = price(model, p, c, self.prices)
            cost = None if (v is None or cost is None) else cost + v
        with self._lock:
            u = self._by.setdefault(form, FormUsage())
            u.calls += 1
            u.failures += 0 if ok else 1
            u.seconds += seconds
            u.prompt_tokens += p_all
            u.completion_tokens += c_all
            if cost is None:
                u.unpriced_calls += 1
            else:
                u.cost += cost
            for model in usage or {}:
                u.models[model] = u.models.get(model, 0) + 1
        return {"prompt_tokens": p_all, "completion_tokens": c_all, "cost_usd": cost, "seconds": seconds}

    def count_item(self) -> None:
        with self._lock:
            self.items += 1

    def summary(self) -> dict[str, Any]:
        """Per-form totals, the grand total and the cost relative to the program (``rigid``) per item."""
        with self._lock:
            forms = {f: u.as_dict() for f, u in sorted(self._by.items())}
            items = self.items
        total = FormUsage()
        for u in self._by.values():
            total.calls += u.calls
            total.failures += u.failures
            total.seconds += u.seconds
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.cost += u.cost
            total.unpriced_calls += u.unpriced_calls
        out: dict[str, Any] = {"items": items, "forms": forms, "total": total.as_dict()}
        rigid = self._by.get("rigid")
        if rigid and rigid.calls and rigid.cost > 0 and items:
            out["cost_vs_program"] = round(total.cost / (rigid.cost / rigid.calls * items), 3)
        return out


@contextmanager
def timed() -> Iterator[list[float]]:
    box = [0.0]
    t = time.perf_counter()
    try:
        yield box
    finally:
        box[0] = time.perf_counter() - t
