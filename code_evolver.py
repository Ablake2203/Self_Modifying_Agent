"""
CodeEvolver — Axis 2 self-modification.

Reads a file from the allowlist, proposes an improved version based on
failure patterns, then hands off to sandbox for validation and deployment.
"""

import ast
import difflib
import re
from pathlib import Path

import config
from llm import call_judge_llm as call_llm
from sandbox import validate_and_deploy

ROOT = Path(__file__).parent

_SYSTEM = """\
You are a Python code improver. You will receive:
  1. A Python source file
  2. The public functions that MUST be preserved (names + signatures)
  3. A failure analysis showing what the system is getting wrong

Your job: rewrite the file to address the failures.

Rules:
- Output ONLY the complete new Python file — no explanation, no markdown, no preamble
- Every function listed under REQUIRED INTERFACE must appear in your output with the same name and signature
- Do not import new third-party libraries
- Make the smallest change that addresses the failure pattern\
"""

_USER_TMPL = """\
FILE: {filepath}

REQUIRED INTERFACE (these functions must exist unchanged in your output):
{required_interface}

CURRENT CONTENT:
---
{current_content}
---

FAILURE ANALYSIS:
Condition: {condition}
Dominant failure reason: {dominant_reason}
Average score this generation: {avg_score:.3f}
Score distribution: {reason_counts}

TASK:
Rewrite this file to reduce the dominant failure reason above.
Output ONLY the complete new Python file content.\
"""


def _extract_required_interface(filepath: str) -> list[str]:
    """
    Scan all .py files in ROOT for 'from <module> import a, b, c' and return
    the names that other modules actually import from filepath.
    These are the only names the proposed rewrite must preserve.
    """
    module_name = Path(filepath).stem
    pattern     = re.compile(rf"from\s+{re.escape(module_name)}\s+import\s+(.+)")
    required: set[str] = set()

    for py_file in ROOT.glob("*.py"):
        if py_file.name == filepath:
            continue
        for line in py_file.read_text(encoding="utf-8").splitlines():
            m = pattern.match(line.strip())
            if m:
                for name in m.group(1).split(","):
                    required.add(name.strip())

    return sorted(required)


def _check_interface(required_names: list[str], proposed: str) -> list[str]:
    """Return names from required_names missing in proposed content."""
    return [n for n in required_names if f"def {n}" not in proposed]


def _count_changed_lines(original: str, proposed: str) -> int:
    diff = list(difflib.unified_diff(
        original.splitlines(), proposed.splitlines()
    ))
    return sum(1 for l in diff if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))


def propose_new_content(
    filepath: str,
    failure_profile: dict,
    condition: str,
) -> str | None:
    """Ask the LLM to rewrite filepath based on the failure profile. Returns proposed content or None."""
    path = ROOT / filepath
    if not path.exists():
        print(f"           [code-evolver] {filepath} not found — skipping.")
        return None

    current_content  = path.read_text(encoding="utf-8")
    required_fns     = _extract_required_interface(filepath)
    required_block   = "\n".join(f"  def {n}(...)" for n in required_fns) or "  (none)"

    user_msg = _USER_TMPL.format(
        filepath=filepath,
        required_interface=required_block,
        current_content=current_content,
        condition=condition,
        dominant_reason=failure_profile.get("dominant_reason", "unknown"),
        avg_score=failure_profile.get("avg_score", 0.0),
        reason_counts=failure_profile.get("reason_counts", {}),
    )

    raw = call_llm(_SYSTEM, user_msg, max_tokens=config.CODE_EVOLVE_MAX_TOKENS)

    # Strip markdown fences if the LLM added them
    content = raw.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(
            l for l in lines
            if not l.strip().startswith("```")
        ).strip()

    # Interface check — all public functions must be present
    missing = _check_interface(required_fns, content)
    if missing:
        print(f"           [code-evolver] Missing required functions {missing} — discarding.")
        return None

    # Enforce max-diff constraint
    changed = _count_changed_lines(current_content, content)
    if changed > config.CODE_EVOLVE_MAX_LINES:
        print(f"           [code-evolver] Proposed diff too large ({changed} lines, limit {config.CODE_EVOLVE_MAX_LINES}) — discarding.")
        return None

    print(f"           [code-evolver] Proposed {changed} line(s) changed in {filepath}.")
    return content


def run_code_evolution(
    filepath: str,
    failure_profile: dict,
    condition: str,
    baseline_score: float,
    generation: int,
) -> tuple[bool, float]:
    """
    Full pipeline: propose → validate → deploy.
    Returns (deployed, resulting_score).
    """
    print(f"           [code-evolver] Proposing rewrite of {filepath}...")
    proposed = propose_new_content(filepath, failure_profile, condition)

    if proposed is None:
        return False, baseline_score

    return validate_and_deploy(
        filepath=filepath,
        new_content=proposed,
        condition=condition,
        baseline_score=baseline_score,
        generation=generation,
    )
