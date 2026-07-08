"""
Checkpoint persistence and regression alerts for the continuous loop.
"""

import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path("state.json")
ALERTS_DIR = Path("alerts")


def save(data: dict, path: Path = STATE_PATH) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(path: Path = STATE_PATH) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_alert(message: str) -> Path:
    ALERTS_DIR.mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = ALERTS_DIR / f"alert_{ts}.md"
    path.write_text(f"# Alert — {ts}\n\n{message}\n", encoding="utf-8")
    return path


def clear(path: Path = STATE_PATH) -> None:
    if path.exists():
        path.unlink()
