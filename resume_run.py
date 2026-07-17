"""
Resume a crashed run from its runs/<condition>_<ts>.json store.

The per-generation store contains everything run_experiment() needs to
continue: current prompt/template/reflection, per-gen scores and task
results. This script reconstructs the checkpoint dict that
run_experiment(checkpoint=...) expects and continues appending to the
SAME store file from the next generation.

Usage:
    python resume_run.py runs/biased_20260716_163550.json

Notes:
  - Does NOT touch state0/ snapshots — the working tree is resumed as-is.
  - RANDOM_SEED is re-applied at resume, so the training-task sampling
    sequence differs from an uninterrupted run. Adoption decisions are
    unaffected (validation is deterministic and uses fixed tasks).
  - code_stagnation / tool-evolver counters are reset conservatively to 0
    (worst case: Axis 2/3 fire a couple of generations later than they
    would have in an uninterrupted run).
"""

import argparse
import json
from pathlib import Path

import config
from evolution import run_experiment, _compute_failure_profile


def build_checkpoint(store_path: Path) -> dict:
    entries = json.loads(store_path.read_text())
    if not entries:
        raise SystemExit(f"{store_path} is empty — nothing to resume.")
    last = entries[-1]
    condition = last["condition"]
    last_gen  = last["generation"]

    history_prompt = []
    for e in entries:
        if e["generation"] == 0:
            continue
        history_prompt.append({
            "generation":      e["generation"],
            "prompt":          e["prompt"],
            "avg_score":       e.get("avg_feedback") or 0.0,
            "failure_profile": (_compute_failure_profile(e["task_results"])
                                if e.get("task_results") else {}),
        })

    # pending DARA thoughts + adoption counters reset at every meta-reflect
    last_meta = (last_gen // config.META_REFLECT_EVERY) * config.META_REFLECT_EVERY
    pending_dara, adopt_wins, adopt_total = [], 0, 0
    for e in entries:
        if e["generation"] > last_meta:
            pending_dara.extend(e.get("dara_thoughts") or [])
            for c in e.get("candidates") or []:
                adopt_total += 1
                adopt_wins  += int(bool(c.get("adopted")))

    last_profile = history_prompt[-1]["failure_profile"] if history_prompt else {}

    return {
        "generation":            last_gen,
        "condition":             condition,
        "current_prompt":        last["prompt"],
        "current_reflection":    last["reflection"],
        "history_prompt":        history_prompt,
        "history_reflection":    [],
        "pending_dara":          pending_dara,
        "adopt_wins":            adopt_wins,
        "adopt_total":           adopt_total,
        "code_stagnation_count": 0,
        "allowlist_index":       0,
        "same_reason_count":     0,
        "last_dominant_reason":  last_profile.get("dominant_reason", ""),
        "last_accuracy":         last.get("accuracy"),
        "store_path":            str(store_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume a crashed run from its store JSON")
    parser.add_argument("store", type=str, help="runs/<condition>_<ts>.json to resume")
    args = parser.parse_args()

    store_path = Path(args.store)

    # Exclusive lock — a suspended process can wake and keep writing, so two
    # resumers on one store would interleave duplicate generations (this
    # happened on 2026-07-17; see *_raw_interleaved.json).
    lock = store_path.with_suffix(".lock")
    if lock.exists():
        pid = lock.read_text().strip()
        import subprocess
        alive = subprocess.run(["kill", "-0", pid], capture_output=True).returncode == 0
        if alive:
            raise SystemExit(f"Another resume (pid {pid}) is writing {store_path} — refusing.")
        print(f"Stale lock from dead pid {pid} — taking over.")
    import os
    lock.write_text(str(os.getpid()))

    try:
        checkpoint = build_checkpoint(store_path)
        cond, gen  = checkpoint["condition"], checkpoint["generation"]
        if gen >= config.NUM_GENERATIONS:
            raise SystemExit(f"{store_path} already has all {gen} generations — nothing to resume.")
        print(f"Resuming {cond} from generation {gen + 1}/{config.NUM_GENERATIONS} "
              f"(store: {store_path})")
        run_experiment(cond, checkpoint=checkpoint)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
