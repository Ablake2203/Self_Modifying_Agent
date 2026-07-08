"""
Generate 180 additional benchmark tasks using Claude Haiku.
Appends them to the existing 20 in benchmark.py → total 200.

Usage:
    python generate_benchmark.py

Requires JUDGE_API_KEY (Claude) set in .env.
Output: generated_tasks.json  (inspect before committing to benchmark.py)
"""

import json
import re
import time
from pathlib import Path
from llm import call_judge_llm as call_llm

# Distribution across 180 new tasks
CATEGORIES = {
    "security":        45,   # sql injection variants, auth bypass, path traversal, deserialization, etc.
    "correctness":     45,   # off-by-one, mutable defaults, None checks, float equality, race conditions
    "maintainability": 45,   # resource leaks, bare excepts, magic numbers, god functions, dead code
    "clean":           45,   # genuinely clean code — agent must NOT flag anything
}

BATCH_SIZE = 5  # tasks per LLM call

# ── Prompts ──────────────────────────────────────────────────────────────────

_SYSTEM = """\
You are a Python code snippet generator for a benchmark dataset.
You write realistic, short Python functions (10-25 lines) for evaluating AI code reviewers.
Each snippet must be subtle — not a textbook example. A junior dev might miss it.
Output valid JSON only. No explanation, no markdown fences.\
"""

_USER_ISSUE = """\
Generate {n} Python code snippets with REAL {category} issues.

Rules:
- Each snippet: a realistic function, 10-25 lines, plausible real-world use
- Issue must be subtle — not immediately obvious
- No famous textbook examples (no basic "SELECT * WHERE name='" SQL injection)
- issue_keywords: 3-5 lowercase substrings a good reviewer would use when flagging it

Output a JSON array of {n} objects, each with these exact fields:
{{
  "id": "unique_snake_case_id",
  "code": "the python code as a string with \\n for newlines",
  "has_issue": true,
  "issue_type": "{category}",
  "severity": "{severity}",
  "issue_desc": "one sentence describing the exact issue",
  "issue_keywords": ["kw1", "kw2", "kw3"]
}}

Category: {category}
Severity: {severity}
Examples of issue types to cover (vary across the {n} snippets):
{examples}
"""

_USER_CLEAN = """\
Generate {n} Python code snippets that are GENUINELY CLEAN — no real bugs or vulnerabilities.

Rules:
- Each snippet: a realistic function, 10-25 lines, plausible real-world use
- Must be actually correct — no subtle bugs, no security issues
- Should look like it MIGHT have issues (to challenge the reviewer) but genuinely doesn't
- Varied domains: web, data processing, file I/O, algorithms, config parsing

Output a JSON array of {n} objects, each with these exact fields:
{{
  "id": "unique_snake_case_id",
  "code": "the python code as a string with \\n for newlines",
  "has_issue": false,
  "issue_type": "clean",
  "severity": "none",
  "issue_desc": "clean — no issues",
  "issue_keywords": []
}}
"""

CATEGORY_CONFIG = {
    "security": {
        "severity": "critical",
        "examples": (
            "- second-order SQL injection\n"
            "- timing attack on token comparison\n"
            "- path traversal via unsanitised filename\n"
            "- insecure deserialization\n"
            "- SSRF via user-controlled URL\n"
            "- JWT algorithm confusion\n"
            "- XML external entity (XXE)\n"
            "- command injection via subprocess\n"
            "- open redirect\n"
            "- weak PRNG for secrets"
        ),
    },
    "correctness": {
        "severity": "medium",
        "examples": (
            "- mutable default argument\n"
            "- off-by-one in slice/range\n"
            "- float equality comparison\n"
            "- missing None check before attribute access\n"
            "- integer overflow in bitshift\n"
            "- unhandled StopIteration\n"
            "- wrong variable captured in closure\n"
            "- dict modified during iteration\n"
            "- incorrect use of is vs ==\n"
            "- thread-unsafe counter without lock"
        ),
    },
    "maintainability": {
        "severity": "low",
        "examples": (
            "- resource leak (file/socket not closed)\n"
            "- bare except clause swallowing all errors\n"
            "- magic number with no constant\n"
            "- function doing too many unrelated things\n"
            "- dead code after return\n"
            "- deeply nested conditionals\n"
            "- unused import\n"
            "- string concatenation in loop\n"
            "- hardcoded path or credential\n"
            "- missing error handling on external call"
        ),
    },
}


def _parse_json_array(raw: str) -> list[dict]:
    """Extract JSON array from LLM output, stripping any prose around it."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("```"))
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in output:\n{raw[:300]}")
    return json.loads(match.group(0))


def _generate_batch(category: str, n: int, existing_ids: set[str]) -> list[dict]:
    """Generate one batch of tasks for a category."""
    if category == "clean":
        user_msg = _USER_CLEAN.format(n=n)
    else:
        cfg = CATEGORY_CONFIG[category]
        user_msg = _USER_ISSUE.format(
            n=n,
            category=category,
            severity=cfg["severity"],
            examples=cfg["examples"],
        )

    raw = call_llm(_SYSTEM, user_msg, max_tokens=4000)
    tasks = _parse_json_array(raw)

    # Deduplicate IDs
    clean = []
    for t in tasks:
        if t["id"] in existing_ids:
            t["id"] = t["id"] + "_v2"
        existing_ids.add(t["id"])
        clean.append(t)
    return clean


def generate_all() -> list[dict]:
    all_tasks = []
    existing_ids: set[str] = set()

    for category, total in CATEGORIES.items():
        print(f"\n[generate] Category: {category} ({total} tasks, {total // BATCH_SIZE} batches)")
        batches_done = 0
        collected = 0

        while collected < total:
            batch_n = min(BATCH_SIZE, total - collected)
            print(f"  batch {batches_done + 1}: generating {batch_n} tasks...", end=" ", flush=True)
            try:
                batch = _generate_batch(category, batch_n, existing_ids)
                all_tasks.extend(batch)
                collected += len(batch)
                batches_done += 1
                print(f"done ({len(batch)} tasks, total {collected}/{total})")
            except Exception as e:
                print(f"FAILED: {e}")
                print("  retrying in 5s...")
                time.sleep(5)

            time.sleep(1)  # rate limit buffer

    return all_tasks


def main():
    print("Generating 180 benchmark tasks via Claude Haiku...")
    print("Existing 20 tasks in benchmark.py will be kept — these are additions.\n")

    tasks = generate_all()

    out = Path("generated_tasks.json")
    out.write_text(json.dumps(tasks, indent=2))
    print(f"\n✓ {len(tasks)} tasks saved to {out}")
    print("Next: review generated_tasks.json, then run:")
    print("  python append_benchmark.py")


if __name__ == "__main__":
    main()
