"""TRIBES: an optimizer-agnostic, never-worse layer on top of an optimized DSPy program.

The optimized program (from GEPA, MIPROv2, SIMBA, ...) stays as one of three forms; a ReAct reviewer of its draft and a
ReAct agent are added, and a label-free rule picks one output per input. An evidence-gated verifier can settle the
contested inputs. A task-level non-inferiority test on labeled selection data switches the layer off where it does not
help, so the program is never replaced by something worse on that data.
"""
__version__ = "1.2.6"

from . import tasks  # noqa: E402
from .callbacks import Callback, JSONLCallback, LoggingCallback  # noqa: E402
from .context import current_inputs, item_context, item_tool  # noqa: E402
from .core import Selection, Tribes  # noqa: E402

PeachTrees = Tribes  # the name up to 1.0, kept for compatibility
from .forms import Assembled, Liquid, run_python, steps  # noqa: E402
from .replay import replay, replay_protocol  # noqa: E402
from .select import (  # noqa: E402
    FORMS,
    contested,
    do_no_harm,
    explain_pick,
    non_inferior,
    non_inferiority,
    paired_stats,
    pick,
    survivors,
    switch_power,
    task_switch,
    text_key,
)
from .tasks import Task  # noqa: E402
from .usage import Ledger  # noqa: E402
from .verify import Verdict, Verifier, VerifierGate  # noqa: E402

__all__ = ["Tribes", "PeachTrees", "Selection", "Task", "tasks", "Verifier", "VerifierGate", "Verdict", "Assembled",
           "Liquid",
           "run_python", "steps", "Callback", "LoggingCallback", "JSONLCallback", "Ledger", "current_inputs",
           "item_context", "item_tool", "replay", "replay_protocol", "FORMS", "pick", "explain_pick", "contested",
           "survivors", "non_inferior", "do_no_harm", "non_inferiority", "task_switch", "switch_power", "paired_stats",
           "text_key"]
