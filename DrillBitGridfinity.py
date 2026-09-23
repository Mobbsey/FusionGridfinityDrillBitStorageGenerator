"""Autodesk Fusion entry point for Drill Bit Gridfinity."""

from . import commands
from .lib import fusion360utils as futil


def run(context):
    """Start the add-in and register its commands."""
    try:
        futil.log("Starting Drill Bit Gridfinity")
        commands.start()
    except Exception:
        futil.handle_error("add-in start", show_message_box=True)


def stop(context):
    """Stop the add-in and release all registered resources."""
    try:
        commands.stop()
        futil.clear_handlers()
        futil.log("Stopped Drill Bit Gridfinity")
    except Exception:
        futil.handle_error("add-in stop", show_message_box=True)
