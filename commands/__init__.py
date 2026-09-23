"""Command registry for the add-in."""

from __future__ import annotations

from . import create_bins

commands = [
    create_bins,
]


def start() -> None:
    """Start every registered command, rolling back on partial failure."""
    started = []
    try:
        for command in commands:
            command.start()
            started.append(command)
    except Exception:
        for command in reversed(started):
            command.stop()
        raise


def stop() -> None:
    """Stop every registered command in reverse registration order."""
    first_error = None
    for command in reversed(commands):
        try:
            command.stop()
        except Exception as error:  # Continue cleaning up the remaining commands.
            if first_error is None:
                first_error = error
    if first_error is not None:
        raise first_error
