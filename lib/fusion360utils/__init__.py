"""Minimal utilities patterned after Autodesk's current Python add-in template."""

from .event_utils import add_handler, clear_handlers
from .general_utils import handle_error, log

__all__ = ["add_handler", "clear_handlers", "handle_error", "log"]
