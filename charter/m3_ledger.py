"""M3 — Declared Commitment Ledger (E-channel, spec §5.3).

Human-gold annotation of every distinct prompt against the charter. Sheets are
PRE-FILLED (Claude-assisted gold, per the 2026-07-29 session decision) and the
user verifies/corrects — recorded as a limitation in the framework doc. The
loader refuses incomplete sheets so unverified rows can't slip into verdicts.
"""

import csv
import json
from pathlib import Path

from charter.charter_v1 import CHARTER_VERSION, CONSTRAINTS, SCORED
from charter.prompts_index import index_prompts

SHEET_CSV = Path(__file__).parent / "fixtures" / "m3_sheet.csv"
SHEET_MD = Path(__file__).parent / "fixtures" / "m3_prompts.md"

JUDGMENTS = ("present", "weakened", "absent")
E_SCORE = {"present": 1.0, "weakened": 0.5, "absent": 0.0}


def generate_sheet(prefill: dict[str, dict[str, str]] | None = None,
                   births: dict[str, str] | None = None) -> None:
    """Write the annotation CSV (one row per prompt x scored constraint) and a
    companion md with full prompt texts. prefill: {prompt_id: {cid: judgment}}."""
    prefill = prefill or {}
    births = births or {}
    index = index_prompts()
    with open(SHEET_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prompt_id", "constraint", "constraint_text",
                    "judgment", "births", "verified"])
        for pid, rec in sorted(index.items()):
            for cid in SCORED:
                w.writerow([pid, cid, CONSTRAINTS[cid]["text"],
                            prefill.get(pid, {}).get(cid, ""),
                            births.get(pid, "") if cid == SCORED[0] else "",
                            ""])
    with open(SHEET_MD, "w") as f:
        f.write(f"# M3 prompt texts (charter {CHARTER_VERSION})\n\n"
                "Companion to m3_sheet.csv. For each prompt below, judge every "
                "charter constraint present / weakened / absent, and note any "
                "new commitments (births). Mark rows verified with 'x'.\n")
        for pid, rec in sorted(index.items()):
            occs = ", ".join(f"{r}@g{g}" for r, g in rec["occurrences"][:6])
            more = "" if len(rec["occurrences"]) <= 6 else f" (+{len(rec['occurrences']) - 6} more)"
            f.write(f"\n---\n\n## {pid}\nSeen: {occs}{more}\n\n```\n{rec['text']}\n```\n")


def load_annotations(require_verified: bool = True) -> dict:
    """{prompt_id: {constraint: judgment}} plus births.

    Rows with a blank judgment are collected as `missing` (not-yet-annotated
    prompts, e.g. the v1-era backlog) rather than fatal; a row with a judgment
    but an invalid value is always fatal. require_verified=False accepts
    Claude-prefilled rows before the user's verification pass (results are
    then Claude-assisted gold — flagged in the report)."""
    if not SHEET_CSV.exists():
        raise FileNotFoundError(f"annotation sheet missing: {SHEET_CSV}")
    out: dict[str, dict[str, str]] = {}
    births: dict[str, str] = {}
    missing: list[str] = []
    unverified: list[str] = []
    with open(SHEET_CSV) as f:
        for row in csv.DictReader(f):
            pid, cid, j = row["prompt_id"], row["constraint"], row["judgment"].strip().lower()
            if not j:
                missing.append(f"{pid}/{cid}")
                continue
            if j not in JUDGMENTS:
                raise ValueError(f"invalid judgment: {pid}/{cid} = {j!r}")
            if row.get("verified", "").strip().lower() not in ("x", "yes", "y", "1"):
                unverified.append(f"{pid}/{cid}")
                if require_verified:
                    continue
            out.setdefault(pid, {})[cid] = j
            if row.get("births", "").strip():
                births[pid] = row["births"].strip()
    return {"judgments": out, "births": births, "missing": missing,
            "unverified": unverified,
            "e_scores": {pid: {c: E_SCORE[j] for c, j in cs.items()}
                         for pid, cs in out.items()}}
