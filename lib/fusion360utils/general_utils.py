"""Logging and traceback reporting for Fusion callbacks."""

from __future__ import annotations

import traceback

import adsk.core

from ... import config


def log(message: str, *, debug_only: bool = False) -> None:
    """Write a diagnostic message to Fusion's Text Commands output."""
    if debug_only and not config.DEBUG:
        return

    text = f"[{config.ADDIN_DISPLAY_NAME}] {message}"
    app = adsk.core.Application.get()
    if app:
        app.log(text)
    else:
        print(text)


def handle_error(name: str, *, show_message_box: bool = False) -> str:
    """Log the current exception with a traceback and optionally alert the user."""
    details = traceback.format_exc()
    message = f"Unexpected error in {name}:\n{details}"
    log(message)

    if show_message_box:
        app = adsk.core.Application.get()
        ui = app.userInterface if app else None
        if ui:
            ui.messageBox(
                f"{config.ADDIN_DISPLAY_NAME} encountered an unexpected error.\n\n"
                "See the Text Commands window for the full traceback."
            )
    return details
