"""Exact commands only; wake-word gating lives in the audio adapter."""
from .control import Mode


def parse_command(text):
    words = " ".join(text.lower().strip().split())
    if words.startswith("hey arduino "):
        words = words[len("hey arduino "):]
    return {"auto pilot": Mode.AUTO, "autopilot": Mode.AUTO,
            "object track": Mode.TRACK, "stop": Mode.STOP}.get(words)
