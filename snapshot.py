"""
State-0 snapshot — guarantees every condition starts from an identical baseline
and independently observable evolved states are preserved per condition per seed.

Layout:
  state0/                         frozen baseline, written once, never overwritten
  evolved/<condition>_seed<N>/    final evolved state of each condition per seed

Flow per run:
  1. snapshot.save()              — idempotent: only writes state0/ if it doesn't exist yet
  2. snapshot.restore()           — before each condition run (clean slate)
  3. ... condition runs, Axis 2 may modify files freely ...
  4. snapshot.save_evolved(c, s)  — after condition run, preserves what it evolved

To hard-reset state-0 (e.g. after intentional baseline changes):
  python -c "import snapshot; snapshot.reset()"
  or: rm -rf state0/ && python main.py ...
"""

import json
import shutil
from pathlib import Path

import config

_STATE0_DIR  = Path("state0")
_EVOLVED_DIR = Path("evolved")

# All files that can be modified during a run — source files + tool registry
_EVOLVABLE_FILES = config.CODE_EVOLVE_ALLOWLIST + ["tools/registry.json"]


def _state0_is_populated() -> bool:
    """Return True if state0/ exists and contains all expected files."""
    if not _STATE0_DIR.exists():
        return False
    for fname in _EVOLVABLE_FILES:
        if not (_STATE0_DIR / Path(fname).name).exists():
            return False
    return True


def save() -> None:
    """
    Freeze all evolvable files as state-0. Idempotent — skips if state0/ is
    already populated. Call reset() to explicitly recreate it.
    """
    if _state0_is_populated():
        print(f"  [snapshot] state-0 already exists — skipping save (call reset() to recreate)")
        return
    _STATE0_DIR.mkdir(exist_ok=True)
    for fname in _EVOLVABLE_FILES:
        src = Path(fname)
        if src.exists():
            shutil.copy2(src, _STATE0_DIR / Path(fname).name)
    print(f"  [snapshot] state-0 saved: {_EVOLVABLE_FILES}")


def restore() -> None:
    """Restore all evolvable files from state-0. Called before every condition run."""
    if not _state0_is_populated():
        print("  [snapshot] WARNING: state0/ missing or incomplete — run snapshot.reset() first.")
        return
    for fname in _EVOLVABLE_FILES:
        snap   = _STATE0_DIR / Path(fname).name
        target = Path(fname)
        if snap.exists():
            shutil.copy2(snap, target)
        elif target.exists():
            target.unlink()  # file didn't exist at state-0, remove if created during run
    print(f"  [snapshot] state-0 restored: {_EVOLVABLE_FILES}")


def reset() -> None:
    """
    Hard-reset state-0 from current disk state. Wipes state0/ and rewrites it.
    Use this after intentional baseline changes (e.g. editing evolution.py).
    registry.json is always reset to empty {} — seed tools load from seed.py, not JSON.
    """
    if _STATE0_DIR.exists():
        shutil.rmtree(_STATE0_DIR)
    _STATE0_DIR.mkdir()

    for fname in _EVOLVABLE_FILES:
        src = Path(fname)
        if fname == "tools/registry.json":
            # Seed tools are always loaded from seed.py — registry.json only holds
            # agent-created tools. Clean state is always empty.
            (_STATE0_DIR / "registry.json").write_text("{}")
        elif src.exists():
            shutil.copy2(src, _STATE0_DIR / Path(fname).name)

    print(f"  [snapshot] state-0 hard reset: {_EVOLVABLE_FILES}")
    print(f"  [snapshot] registry.json → {{}} (seed tools load from seed.py)")


def save_evolved(condition: str, seed: int) -> None:
    """
    Preserve the final evolved state of a condition for later inspection.
    Saved to evolved/<condition>_seed<N>/.
    """
    dest = _EVOLVED_DIR / f"{condition}_seed{seed}"
    dest.mkdir(parents=True, exist_ok=True)
    for fname in _EVOLVABLE_FILES:
        src = Path(fname)
        if src.exists():
            shutil.copy2(src, dest / Path(fname).name)
    print(f"  [snapshot] evolved state saved → evolved/{condition}_seed{seed}/")
