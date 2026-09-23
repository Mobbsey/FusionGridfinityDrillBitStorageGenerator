"""Fusion event registration with strong-reference retention and cleanup."""

from __future__ import annotations

import sys
from collections.abc import Callable

from .general_utils import handle_error, log

HandlerReference = tuple[object, object]
_handlers: list[HandlerReference] = []


def add_handler(
    event,
    callback: Callable,
    *,
    name: str | None = None,
    local_handlers: list | None = None,
):
    """Attach a callback and retain the Python handler for Fusion's lifetime.

    Passing ``local_handlers`` lets a command own and release its handlers
    independently. Otherwise the handler is retained until add-in shutdown.
    """
    handler_type = _resolve_handler_type(event)
    handler_name = name or handler_type.__name__

    class Handler(handler_type):
        def __init__(self):
            super().__init__()

        def notify(self, args):
            try:
                callback(args)
            except Exception:
                handle_error(handler_name)

    handler = Handler()
    event.add(handler)
    references = local_handlers if local_handlers is not None else _handlers
    references.append((event, handler))
    return handler


def clear_handlers(local_handlers: list | None = None) -> None:
    """Detach and release all handlers in the supplied or global collection."""
    references = local_handlers if local_handlers is not None else _handlers
    for event, handler in reversed(references[:]):
        try:
            event.remove(handler)
        except Exception as error:
            # Destroying a command also destroys its events. Removal can then
            # fail harmlessly; the retained Python reference must still go.
            log(f"Event handler was already unavailable during cleanup: {error}")
    references.clear()


def _resolve_handler_type(event):
    """Resolve the generated Fusion handler class across API/Python versions."""
    annotation = getattr(event.add, "__annotations__", {}).get("handler")
    if isinstance(annotation, type):
        return annotation

    module = sys.modules.get(event.__module__)
    if isinstance(annotation, str) and module is not None:
        type_name = annotation.replace("::", ".").split(".")[-1]
        annotated_type = getattr(module, type_name, None)
        if isinstance(annotated_type, type):
            return annotated_type

    # Generated event classes follow EventName -> EventNameHandler. This also
    # covers current annotations such as "adsk.core.CommandEventHandler".
    event_type_name = type(event).__name__
    fallback_name = f"{event_type_name}Handler"
    fallback_type = getattr(module, fallback_name, None) if module else None
    if isinstance(fallback_type, type):
        return fallback_type

    raise TypeError(f"Unable to resolve a handler type for {event_type_name}.")
