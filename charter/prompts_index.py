"""Index the distinct prompts across runs/*.json and their adoption events.

Adoption-event indexing (spec §6.2): the policy is piecewise-constant in the
prompt, so batteries run once per distinct prompt and results are mapped back
onto the generation axis through this index.
"""

import hashlib
import json
from pathlib import Path

RUNS_DIR = Path(__file__).parent.parent / "runs"


def prompt_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def _gen_files(runs_dir: Path = RUNS_DIR) -> list[Path]:
    """Run files whose schema is a list of generation entries with prompts."""
    out = []
    for p in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict) \
                and "prompt" in data[0] and "generation" in data[0]:
            out.append(p)
    return out


def index_prompts(runs_dir: Path = RUNS_DIR) -> dict:
    """{prompt_id: {text, occurrences: [(run_name, generation), ...]}}"""
    index: dict[str, dict] = {}
    for path in _gen_files(runs_dir):
        data = json.loads(path.read_text())
        for entry in data:
            text = entry.get("prompt")
            if not text:
                continue
            pid = prompt_id(text)
            rec = index.setdefault(pid, {"text": text, "occurrences": []})
            rec["occurrences"].append((path.stem, entry["generation"]))
    return index


def adoption_events(run_path: Path) -> list[dict]:
    """[(generation, old_prompt_id, new_prompt_id)] for one run, in order."""
    data = json.loads(Path(run_path).read_text())
    events = []
    prev = None
    for entry in data:
        text = entry.get("prompt")
        if text is None:
            continue
        pid = prompt_id(text)
        if prev is not None and pid != prev:
            events.append({
                "generation": entry["generation"],
                "old": prev,
                "new": pid,
            })
        prev = pid
    return events


def distinct_prompts(run_path: Path) -> list[dict]:
    """Ordered distinct consecutive prompts of one run:
    [{prompt_id, text, first_gen, last_gen}]"""
    data = json.loads(Path(run_path).read_text())
    out: list[dict] = []
    for entry in data:
        text = entry.get("prompt")
        if text is None:
            continue
        pid = prompt_id(text)
        if out and out[-1]["prompt_id"] == pid:
            out[-1]["last_gen"] = entry["generation"]
        else:
            out.append({"prompt_id": pid, "text": text,
                        "first_gen": entry["generation"],
                        "last_gen": entry["generation"]})
    return out
