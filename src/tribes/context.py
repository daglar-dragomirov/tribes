"""The inputs of the item being processed, visible to per-item tools.

ReAct tools are fixed when an agent is built, but many task tools depend on the item: the database of a text-to-SQL
question, the public tests of a coding problem. TRIBES sets the current inputs for the duration of every form and
verifier call; a tool reads them with :func:`current_inputs`. The value is a context variable, so it is correct under
threads (TRIBES copies the context into its workers) and under asyncio.
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping

_CURRENT: contextvars.ContextVar[Mapping[str, Any] | None] = contextvars.ContextVar("tribes_inputs", default=None)


def current_inputs() -> Mapping[str, Any]:
    """The inputs of the item whose forms are running now. Raises outside a TRIBES call."""
    v = _CURRENT.get()
    if v is None:
        raise RuntimeError("no current item: per-item tools work only inside a TRIBES call (or item_context)")
    return v


@contextmanager
def item_context(inputs: Mapping[str, Any]) -> Iterator[None]:
    """Make ``inputs`` the current item for the enclosed block (used by TRIBES; handy in tests)."""
    token = _CURRENT.set(dict(inputs))
    try:
        yield
    finally:
        _CURRENT.reset(token)


def item_tool(fn: Callable[..., str], name: str | None = None, doc: str | None = None) -> Callable[..., str]:
    """Turn ``fn(inputs, *args)`` into an agent tool ``tool(*args)`` that reads the current item's inputs.

    >>> def run_sql(inputs, query: str) -> str: ...
    >>> tool = item_tool(run_sql)          # the agent sees run_sql(query)
    """
    import functools
    import inspect

    sig = inspect.signature(fn)
    params = list(sig.parameters.values())[1:]

    @functools.wraps(fn)
    def tool(*args, **kwargs):
        try:
            return fn(current_inputs(), *args, **kwargs)
        except Exception as e:  # a tool never raises into the agent
            return f"error: {type(e).__name__}: {str(e)[:300]}"

    tool.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]
    ann = dict(getattr(fn, "__annotations__", {}))
    first = next(iter(sig.parameters), None)
    ann.pop(first, None)
    tool.__annotations__ = ann
    if name:
        tool.__name__ = tool.__qualname__ = name
    if doc:
        tool.__doc__ = doc
    return tool
