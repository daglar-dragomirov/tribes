"""The three TRIBES forms around an optimized DSPy program.

rigid      the optimized program itself (any optimizer: GEPA, MIPROv2, SIMBA, ...)
assembled  the program's draft, then a ReAct reviewer that checks it and fixes it only if it finds a defect
liquid     a ReAct agent that solves the task from scratch

Both agents get the same task-agnostic instructions: the task's own purpose and the optimizer's learned guidance (the
program's predictor instructions), optional correct outputs of a few labeled examples, and one fixed template per form.
They get ``run_python`` and any task tools you pass.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping, Sequence

import dspy

LIQUID_TEMPLATE = (
    "Accomplish the task described above for the given inputs. Work step by step. If the task depends on information you "
    "do not have, gather it with the available tools first: make several targeted searches or calls, start from what the "
    "inputs name, follow leads found in the results, and base your output on what you found. Use run_python (Python, "
    "standard library only, no network) for any calculation, counting or check. Before giving the final output, check it "
    "against every requirement of the task and fix anything that is wrong or missing. Give the final output in the "
    "required format.")
ASSEMBLED_TEMPLATE = (
    "A fixed pipeline already produced a draft for this task (given in the inputs). Check the draft against every "
    "requirement of the task. If something the task depends on is missing or wrong in the draft, gather what is needed "
    "with the available tools (targeted searches or calls, following leads found in the results) and fix it; use "
    "run_python (Python, standard library only, no network) for any calculation, counting or check. If the draft is "
    "correct, return it unchanged; if you change it, keep its form and length. If you can neither confirm nor fix it, "
    "return the draft unchanged; never replace it with a statement that the answer cannot be determined. Give the final "
    "output in the required format.")

FINAL_TOOLS = ("submit", "finish")


def run_python(code: str) -> str:
    """Run Python 3 code (standard library only, 10 s limit) and return what it prints; use print()."""
    d = tempfile.mkdtemp(prefix="tribes_")
    try:
        p = os.path.join(d, "main.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(code))
        r = subprocess.run([sys.executable, "-I", p], capture_output=True, text=True, timeout=10, cwd=d)
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr[-1500:]) if r.stderr else "")
        return out[-3000:] or "(no output; use print())"
    except subprocess.TimeoutExpired:
        return "[timed out after 10 s]"
    except Exception as e:  # the tool never raises into the agent
        return f"error: {type(e).__name__}: {str(e)[:200]}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def task_text(program: dspy.Module, examples: str | None = None) -> str:
    """The shared head of the agents' instructions: the program's predictor instructions (the task's purpose plus what
    the optimizer learned) and optional correct outputs of labeled examples."""
    parts = [p.signature.instructions.strip() for _, p in program.named_predictors()]
    h = "The task (with the guidance an optimizer learned for it):\n" + "\n\n".join(f"- {x}" for x in parts if x)
    if examples:
        h += ("\n\nCorrect final outputs for other inputs of this task (follow their form and length; no explanations "
              "unless they show some):\n" + examples)
    return h


def label_examples(trainset: Sequence[dspy.Example], output_field: str, k: int = 5, width: int = 150) -> str:
    lines = []
    for ex in list(trainset)[:k]:
        v = ex.get(output_field) if hasattr(ex, "get") else getattr(ex, output_field, None)
        if v not in (None, ""):
            lines.append(f"- {output_field}: {str(v)[:width]}")
    return "\n".join(lines)


def clean(text: Any) -> Any:
    """Strip DSPy field markers and leading quote marks that agents sometimes copy into their output."""
    if not isinstance(text, str):
        return text
    t = re.sub(r"\s*\[\[\s*##[^\]]*\]\]\s*", " ", text).strip()
    return re.sub(r"^(>\s*)+", "", t)


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def steps(r: Any) -> list[dict[str, Any]]:
    """The steps of a ReAct result as dicts ``{thought, tool, args, observation, error}``.

    Reads both DSPy ReAct formats: the ``history`` of tool-call events (DSPy >= 3.5) and the older flat ``trajectory``
    (thought_i / tool_name_i / tool_args_i / observation_i). The final ``submit`` / ``finish`` call is included; callers
    that need evidence filter it out (see :func:`tool_observations`).
    """
    out: list[dict[str, Any]] = []
    messages = _get(_get(r, "history"), "messages")
    if messages:
        for ev in messages:
            if not isinstance(ev, Mapping):
                continue
            thought = ev.get("next_thought")
            tc = ev.get("tool_calls")
            calls = list(_get(tc, "tool_calls") or [])
            results = list(_get(_get(tc, "tool_call_results"), "tool_call_results") or [])
            if not calls and thought:
                out.append({"thought": thought, "tool": None, "args": {}, "observation": None, "error": False})
            for j, c in enumerate(calls):
                res = results[j] if j < len(results) else None
                out.append({"thought": thought if j == 0 else None, "tool": _get(c, "name"),
                            "args": _get(c, "args") or {}, "observation": _get(res, "value"),
                            "error": bool(_get(res, "is_error", False))})
        return out
    tr = _get(r, "trajectory") or {}
    i = 0
    while f"thought_{i}" in tr or f"tool_name_{i}" in tr:
        obs = tr.get(f"observation_{i}")
        out.append({"thought": tr.get(f"thought_{i}"), "tool": tr.get(f"tool_name_{i}"),
                    "args": tr.get(f"tool_args_{i}") or {}, "observation": obs,
                    "error": str(obs).startswith("Execution error")})
        i += 1
    return out


def tool_observations(r: Any) -> list[str]:
    """Observations of successful, non-final tool calls: what the agent's checks actually returned."""
    return [str(s["observation"]) for s in steps(r)
            if s["tool"] and s["tool"] not in FINAL_TOOLS and not s["error"] and s["observation"] not in (None, "")]


def react_text(r: Any) -> str:
    """A compact rendering of a ReAct run: its tool steps and its final reasoning."""
    lines = []
    for s in steps(r):
        if s["tool"] in FINAL_TOOLS:
            continue
        line = f"thought: {str(s['thought'] or '')[:1200]}"
        if s["tool"]:
            line += f"\ncall: {s['tool']}({s['args']}) -> {str(s['observation'])[:400]}"
        lines.append(line)
    return "\n".join(lines + ["final reasoning: " + str(getattr(r, "reasoning", "") or "")[:4000]])


def _signature(input_fields: Sequence[str], extra: Mapping[str, str], output_field: str, instructions: str):
    fields: dict[str, Any] = {k: (str, dspy.InputField()) for k in input_fields}
    for name, desc in extra.items():
        fields[name] = (str, dspy.InputField(desc=desc))
    fields[output_field] = (str, dspy.OutputField(desc="the final output in the required format"))
    return dspy.make_signature(fields, instructions)


class Liquid(dspy.Module):
    """A ReAct agent that solves the task from scratch with the task's instructions and tools."""

    def __init__(self, input_fields: Sequence[str], output_field: str, instructions: str,
                 tools: Sequence[Callable] = (), max_iters: int = 8):
        super().__init__()
        self.input_fields, self.output_field = list(input_fields), output_field
        self.agent = dspy.ReAct(_signature(input_fields, {}, output_field, instructions),
                                tools=list(tools) + [run_python], max_iters=max_iters)

    def forward(self, **kw):
        r = self.agent(**{k: kw[k] for k in self.input_fields})
        return dspy.Prediction(**{self.output_field: clean(getattr(r, self.output_field))}, reasoning=react_text(r))


class Assembled(dspy.Module):
    """The program's draft, then a ReAct reviewer that checks it and changes it only on a found defect."""

    def __init__(self, program: dspy.Module, input_fields: Sequence[str], output_field: str, instructions: str,
                 tools: Sequence[Callable] = (), max_iters: int = 8):
        super().__init__()
        self.program = program
        self.input_fields, self.output_field = list(input_fields), output_field
        extra = {"draft_reasoning": "reasoning of the fixed pipeline", "draft_answer": "output of the fixed pipeline"}
        self.agent = dspy.ReAct(_signature(input_fields, extra, output_field, instructions),
                                tools=list(tools) + [run_python], max_iters=max_iters)

    def forward(self, **kw):
        inputs = {k: kw[k] for k in self.input_fields}
        d = self.program(**inputs)
        draft = getattr(d, self.output_field, None)
        o = self.agent(**inputs, draft_reasoning=str(getattr(d, "reasoning", "") or "")[:6000], draft_answer=str(draft))
        return dspy.Prediction(**{self.output_field: clean(getattr(o, self.output_field))}, draft=draft,
                               draft_prediction=d, reasoning="Draft answer: " + str(draft) + "\n" + react_text(o))
