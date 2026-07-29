"""Load and validate the frozen minimal-pair fixture (spec §5.1).

pairs_v1.json is authored once (Claude Fable 5, 2026-07-29 session), passes the
mechanical gate below, is user-audited via pair_audit_sheet.md, then frozen.
The loader revalidates on every load so silent edits can't slip through.
"""

import ast
import json
from pathlib import Path

PAIRS_PATH = Path(__file__).parent / "fixtures" / "pairs_v1.json"

MAX_DIFF_LINES = 14  # minimal-edit ceiling; most pairs are 1-3 lines, but a few
# structural maintainability fixes (function split, dispatch table) need more.
# Every diff is shown in pair_audit_sheet.md for human review regardless.


def validate_pair(pair: dict) -> list[str]:
    errors = []
    for side in ("s_plus_code", "s_minus_code"):
        try:
            ast.parse(pair[side])
        except SyntaxError as e:
            errors.append(f"{pair['pair_id']}: {side} does not parse: {e}")
    plus = pair["s_plus_code"].splitlines()
    minus = pair["s_minus_code"].splitlines()
    changed = sum(1 for a, b in zip(plus, minus) if a != b) + abs(len(plus) - len(minus))
    if changed == 0:
        errors.append(f"{pair['pair_id']}: sides are identical")
    if changed > MAX_DIFF_LINES:
        errors.append(f"{pair['pair_id']}: diff too large ({changed} lines)")
    sig = pair.get("signature", "")
    if sig:
        if sig not in pair["s_plus_code"]:
            errors.append(f"{pair['pair_id']}: signature not in s_plus")
        if sig in pair["s_minus_code"]:
            errors.append(f"{pair['pair_id']}: signature still in s_minus")
    return errors


def load_pairs(path: Path = PAIRS_PATH) -> list[dict]:
    pairs = json.loads(path.read_text())
    all_errors = []
    for p in pairs:
        all_errors += validate_pair(p)
    if all_errors:
        raise ValueError("pair fixture failed validation:\n" + "\n".join(all_errors))
    return pairs


def pairs_by_id(pairs: list[dict] | None = None) -> dict[str, dict]:
    return {p["pair_id"]: p for p in (pairs or load_pairs())}


def distractor_pool(pairs: list[dict] | None = None) -> list[str]:
    return [p["issue_desc"] for p in (pairs or load_pairs())]
