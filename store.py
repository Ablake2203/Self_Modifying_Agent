"""
Simple JSON store for all generation data.
One file per experiment run, stored in runs/.
"""

import json
import time
from pathlib import Path

import config


def new_run_path(condition: str) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    return config.RUNS_DIR / f"{condition}_{ts}.json"


def load_store(path: Path) -> list[dict]:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_store(path: Path, store: list[dict]) -> None:
    with open(path, "w") as f:
        json.dump(store, f, indent=2)


def append_generation(path: Path, entry: dict) -> None:
    store = load_store(path)
    store.append(entry)
    save_store(path, store)


def make_entry(
    generation: int,
    prompt: str,
    template: str,
    task_results: list[dict],
    accuracy: float | None,
    condition: str,
    reflection: str | None = None,
    candidates: list[dict] | None = None,
    dara_thoughts: list[dict] | None = None,
) -> dict:
    scores = [r["score"] for r in task_results]
    return {
        "generation":        generation,
        "prompt":            prompt,
        "template":          template,
        "reflection":        reflection,
        "condition":         condition,
        "timestamp":         time.strftime("%Y-%m-%dT%H:%M:%S"),
        "avg_feedback":      round(sum(scores) / len(scores), 4) if scores else None,
        "accuracy":          round(accuracy, 4) if accuracy is not None else None,
        "task_results":      task_results,
        "candidates":        candidates or [],
        "dara_thoughts":     dara_thoughts or [],
    }
