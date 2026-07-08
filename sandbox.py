"""
Sandbox — safe file modification with validation and rollback.

Flow:
  1. Syntax check proposed content
  2. Backup original file
  3. Swap candidate in
  4. Run mini benchmark in fresh subprocess
  5. Keep + git commit if score improves; restore backup otherwise
"""

import ast
import importlib
import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def check_syntax(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def _run_mini_benchmark(condition: str, n_tasks: int, seed: int) -> float | None:
    """Run _mini_bench.py in a fresh subprocess. Returns score or None on failure."""
    result = subprocess.run(
        ["python", "_mini_bench.py", condition, str(n_tasks), str(seed)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"           [sandbox]  Mini-bench error:\n{result.stderr[:300]}")
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        print(f"           [sandbox]  Could not parse score: {result.stdout!r}")
        return None


def _git_commit(filepath: str, generation: int, score: float) -> None:
    msg = f"[code-evolver] gen {generation}: deploy {filepath} (score {score:.3f})"
    subprocess.run(["git", "add", filepath], cwd=ROOT, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, capture_output=True)


def validate_and_deploy(
    filepath: str,
    new_content: str,
    condition: str,
    baseline_score: float,
    generation: int,
    n_tasks: int = 5,
    seed: int = 99,
) -> tuple[bool, float]:
    """
    Validate new_content for filepath and deploy if it improves on baseline_score.
    Returns (deployed, candidate_score).
    """
    path   = ROOT / filepath
    backup = ROOT / (filepath + ".backup")

    # 1 — syntax check
    if not check_syntax(new_content):
        print(f"           [sandbox]  Syntax check failed — discarding.")
        return False, baseline_score

    # 2 — backup original
    shutil.copy2(path, backup)

    # 3 — swap candidate in
    path.write_text(new_content, encoding="utf-8")
    print(f"           [sandbox]  Candidate written. Running mini-benchmark ({n_tasks} tasks)...")

    # 4 — validate in fresh subprocess
    candidate_score = _run_mini_benchmark(condition, n_tasks, seed)

    if candidate_score is None:
        print(f"           [sandbox]  Validation failed — restoring backup.")
        shutil.copy2(backup, path)
        backup.unlink(missing_ok=True)
        return False, baseline_score

    print(f"           [sandbox]  Baseline {baseline_score:.3f} → candidate {candidate_score:.3f}")

    # 5 — keep or restore
    if candidate_score > baseline_score:
        backup.unlink(missing_ok=True)
        _git_commit(filepath, generation, candidate_score)
        _reload_module(filepath)
        print(f"           [sandbox]  Deployed, committed, and reloaded.")
        return True, candidate_score
    else:
        shutil.copy2(backup, path)
        backup.unlink(missing_ok=True)
        print(f"           [sandbox]  No improvement — restored original.")
        return False, baseline_score


def _reload_module(filepath: str) -> None:
    """Reload the deployed module in the current process so changes take effect immediately."""
    module_name = Path(filepath).stem
    if module_name in sys.modules:
        try:
            importlib.reload(sys.modules[module_name])
            print(f"           [sandbox]  Module '{module_name}' reloaded in main process.")
        except Exception as e:
            print(f"           [sandbox]  Reload warning: {e}")
