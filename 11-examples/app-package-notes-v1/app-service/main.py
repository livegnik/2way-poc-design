"""Example backend entrypoint for the notes app-service payload."""


def start(context):
    """Initialize the app service with validated runtime context."""
    return {"status": "ready", "service": "notes"}
