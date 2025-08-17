import os

def is_enabled() -> bool:
    return os.getenv("ERASER_ENABLED", "false").lower() == "true"

def export_topology(topology: dict) -> dict:
    return {
        "status": "accepted",
        "message": "Eraser AI export stub; integration not implemented"
    }
