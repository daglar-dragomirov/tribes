"""Events of a TRIBES run.

Subclass :class:`Callback` and override what you need; pass instances as ``Tribes(..., callbacks=[...])``.
Callbacks are called from worker threads; an exception in a callback is logged and never breaks the run. DSPy's own
callbacks (``dspy.settings.callbacks``) keep working underneath for the individual LM and module calls.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import IO, Any, Mapping

log = logging.getLogger("tribes")


class Callback:
    def on_form_start(self, form: str, inputs: Mapping[str, Any]) -> None:
        """A form (``rigid`` / ``assembled`` / ``liquid``) or the ``verifier`` starts on one input."""

    def on_form_end(self, form: str, inputs: Mapping[str, Any], prediction: Any, error: BaseException | None,
                    usage: Mapping[str, Any]) -> None:
        """A form finished (after its retries). ``prediction`` is None if it failed; ``usage`` has tokens, cost, seconds."""

    def on_select(self, inputs: Mapping[str, Any], selection: Any) -> None:
        """The item rule (and the verifier, if any) chose a form; ``selection`` is a :class:`tribes.Selection`."""

    def on_fit_end(self, report: Mapping[str, Any]) -> None:
        """``fit`` decided whether the layer (and the verifier) is used for this task."""


def emit(callbacks, event: str, *args: Any) -> None:
    for cb in callbacks or ():
        try:
            getattr(cb, event)(*args)
        except Exception as e:  # never let observability break inference
            log.warning("callback %s.%s failed: %s", type(cb).__name__, event, e)


class LoggingCallback(Callback):
    """Logs every form call and selection to the ``tribes`` logger."""

    def __init__(self, level: int = logging.INFO):
        self.level = level

    def on_form_end(self, form, inputs, prediction, error, usage):
        log.log(self.level, "form %-9s %s in %.2fs, %s+%s tokens", form, "ok" if prediction is not None else "FAILED",
                usage.get("seconds", 0.0), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    def on_select(self, inputs, selection):
        log.log(self.level, "selected %s (%s)%s", selection.form, selection.reason,
                f", verifier {selection.verifier['choice']}" if selection.verifier else "")

    def on_fit_end(self, report):
        log.log(self.level, "fit: use_layer=%s gain=%+.4f se=%.4f n=%d", report.get("use_layer"),
                report.get("mean_gain", 0.0), report.get("se", 0.0), report.get("n", 0))


class JSONLCallback(Callback):
    """Appends one JSON line per event to a file: a run log that ``tribes`` tools and notebooks can read back."""

    def __init__(self, stream: IO[str]):
        self.stream = stream
        self._lock = threading.Lock()

    def _write(self, row: dict[str, Any]) -> None:
        with self._lock:
            self.stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            self.stream.flush()

    def on_form_end(self, form, inputs, prediction, error, usage):
        self._write({"event": "form", "form": form, "ok": prediction is not None,
                     "error": None if error is None else repr(error)[:300], **usage})

    def on_select(self, inputs, selection):
        self._write({"event": "select", "form": selection.form, "reason": selection.reason,
                     "keys": {k: None if v is None else str(v) for k, v in selection.keys.items()},
                     "verifier": selection.verifier})

    def on_fit_end(self, report):
        self._write({"event": "fit", **{k: v for k, v in report.items() if k != "items"}})
