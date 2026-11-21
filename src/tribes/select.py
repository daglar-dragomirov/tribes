"""TRIBES 1.0 selection rules (label-free at inference).

Item rule (``pick``): 1. drop forms without a usable output; 2. if a task checker is given, drop forms whose output fails
it (keep all if all fail); 3. if at least two surviving forms give the same answer key, return that answer; 4. otherwise
the reviewer ("assembled"), then the program ("rigid"), then the agent ("liquid").

Task rule: the TRIBES policy is used for a task only if, on labeled selection data, it passes one of two switches:

* ``do_no_harm`` (the 1.0 rule, default): mean gain + z * SE >= 0, i.e. the layer is kept unless it is shown worse at a
  one-sided level of about 16 % (z = 1). It is a do-no-harm screen, not a non-inferiority test: it bounds no harm, and
  with ~100 selection items a layer that is truly 5 pp worse passes about half the time. Use :func:`switch_power` to see
  its operating characteristic for your n.
* ``non_inferiority``: mean gain - z * SE >= -margin, a real non-inferiority test with margin ``margin`` (e.g. z = 1.645
  and margin = 0.02 accept the layer only if it is shown to be at most 2 pp worse at the one-sided 5 % level).
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Callable, Hashable, Iterable, Mapping, Sequence

FORMS = ("rigid", "liquid", "assembled")
FALLBACK = ("assembled", "rigid", "liquid")


def text_key(value: Any) -> str:
    """Generic answer key: lower-cased text without punctuation and articles, whitespace collapsed.

    An output that consists only of articles (e.g. the option letter "A") keeps them, so it is not mistaken for an empty
    output.
    """
    o = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    o = " ".join(re.sub(r"[^\w\s]", " ", o.lower()).split())
    stripped = " ".join(re.sub(r"\b(a|an|the)\b", " ", o).split())
    return stripped or o


def _live(alive: Sequence[str], form: str) -> str:
    if form in alive or not alive:
        return form
    return next(f for f in FALLBACK if f in alive)


def survivors(keys: Mapping[str, Hashable | None], checks: Mapping[str, bool | None] | None = None) -> list[str]:
    """Forms with a usable output that do not fail the checker (all usable ones if every one fails it)."""
    alive = [f for f in FORMS if keys.get(f) is not None]
    if checks:
        ok = [f for f in alive if checks.get(f) is not False]
        alive = ok or alive
    return alive


def explain_pick(keys: Mapping[str, Hashable | None], checks: Mapping[str, bool | None] | None = None,
                 use_vote: bool = True) -> tuple[str, str]:
    """``pick`` with the reason: 'vote', 'reviewer', 'fallback' (the reviewer had no usable output) or 'none'."""
    alive = survivors(keys, checks)
    if use_vote:
        groups: dict[Hashable, list[str]] = {}
        for f in alive:
            groups.setdefault(keys[f], []).append(f)
        big = max(groups.values(), key=len) if groups else []
        if len(big) >= 2:
            return ("assembled" if "assembled" in big else big[0]), "vote"
    if not alive:
        return "assembled", "none"
    form = _live(alive, "assembled")
    return form, ("reviewer" if form == "assembled" else "fallback")


def pick(keys: Mapping[str, Hashable | None], checks: Mapping[str, bool | None] | None = None,
         use_vote: bool = True) -> str:
    """Choose one form for one input.

    keys: form name -> answer key of that form's output, or None if the form produced no usable output.
    checks: form name -> result of a deterministic, label-free task checker (True / False / None = unknown).
    use_vote: False gives the "lite" rule (the reviewer, with the liveness / checker fallback).
    """
    return explain_pick(keys, checks, use_vote)[0]


def contested(keys: Mapping[str, Hashable | None], checks: Mapping[str, bool | None] | None = None) -> bool:
    """An input is contested when at least two different answers survive and no two surviving forms agree."""
    alive = survivors(keys, checks)
    distinct = {keys[f] for f in alive}
    return len(distinct) >= 2 and len(distinct) == len(alive)


def paired_stats(deltas: Iterable[tuple[Hashable, float]]) -> tuple[float, float]:
    """Mean and clustered standard error of per-item differences; items sharing a cluster id are one unit."""
    by: dict[Hashable, list[float]] = {}
    for cluster, d in deltas:
        by.setdefault(cluster, []).append(float(d))
    n = sum(len(v) for v in by.values())
    if n == 0:
        return 0.0, 0.0
    m = sum(sum(v) for v in by.values()) / n
    k = len(by)
    if k < 2:
        return m, 0.0
    var = sum((sum(v) - m * len(v)) ** 2 for v in by.values()) * k / (k - 1) / n ** 2
    return m, math.sqrt(var)


def do_no_harm(deltas: Iterable[tuple[Hashable, float]], z: float = 1.0) -> tuple[bool, float, float]:
    """The 1.0 task switch: (use TRIBES?, mean difference, standard error); accepts iff m + z * se >= 0."""
    m, se = paired_stats(deltas)
    return m + z * se >= 0, m, se


non_inferior = do_no_harm  # the 1.0 name, kept for compatibility; see the module docstring


def non_inferiority(deltas: Iterable[tuple[Hashable, float]], z: float = 1.645,
                    margin: float = 0.02) -> tuple[bool, float, float]:
    """A real non-inferiority test: accepts iff m - z * se >= -margin."""
    m, se = paired_stats(deltas)
    return m - z * se >= -margin, m, se


SWITCHES = {"do_no_harm": do_no_harm, "non_inferiority": non_inferiority}


def task_switch(deltas: Iterable[tuple[Hashable, float]], rule: str = "do_no_harm", z: float | None = None,
                margin: float = 0.02) -> tuple[bool, float, float]:
    """Apply the named task switch with its default ``z`` unless one is given."""
    if rule == "do_no_harm":
        return do_no_harm(deltas, 1.0 if z is None else z)
    if rule == "non_inferiority":
        return non_inferiority(deltas, 1.645 if z is None else z, margin)
    raise ValueError(f"unknown task switch {rule!r}; use one of {sorted(SWITCHES)}")


def switch_power(true_gain: float, sd: float, n: int, rule: str = "do_no_harm", z: float | None = None,
                 margin: float = 0.02) -> float:
    """Probability that the switch accepts the layer, under a normal approximation, when the true mean gain is
    ``true_gain`` and per-item differences have standard deviation ``sd`` over ``n`` independent items."""
    se = sd / math.sqrt(max(1, n))
    if se == 0:
        return float(task_switch([(0, true_gain)], rule, z, margin)[0])
    if rule == "do_no_harm":
        zz = 1.0 if z is None else z
        threshold = -zz * se          # accept iff m >= -z * se
    else:
        zz = 1.645 if z is None else z
        threshold = zz * se - margin  # accept iff m >= z * se - margin
    return 0.5 * math.erfc((threshold - true_gain) / (se * math.sqrt(2)))


Checker = Callable[[Mapping[str, Any], Any], "bool | None"]
