"""M1 — Constraint Satisfaction Profile (A-channel, spec §5.1).

Reviews both sides of every minimal pair under the measured prompt at temp 0,
scores each applicable constraint contrastively via the comparer. Uses the
same template fill as evolution.get_review but routed through the call cache
(get_review calls the uncached backend, and measurement must be resumable).
"""

import config
from charter import comparer
from charter.cache import cached_call_llm
from charter.charter_v1 import M1_CONSTRAINTS

# Template kept identical to evolution.T0 so the in-role channel matches the
# experiment's review channel exactly.
from evolution import T0


def review_code(prompt_text: str, code: str, salt: str = "") -> str:
    user_msg = T0.replace("{code}", code)
    return cached_call_llm(prompt_text, user_msg,
                           temperature=config.BENCHMARK_TEMPERATURE, salt=salt)


def run_m1(prompt_text: str, pairs: list[dict], salt: str = "",
           progress: bool = False) -> dict:
    per_pair = []
    tally: dict[str, list[bool]] = {c: [] for c in M1_CONSTRAINTS}
    for i, pair in enumerate(pairs):
        rp = review_code(prompt_text, pair["s_plus_code"], salt=salt)
        rm = review_code(prompt_text, pair["s_minus_code"], salt=salt)
        scores: dict[str, bool | None] = {}
        for cid in M1_CONSTRAINTS:
            sat = comparer.score_pair(cid, pair, rp, rm)
            scores[cid] = sat
            if sat is not None:
                tally[cid].append(sat)
        per_pair.append({
            "pair_id": pair["pair_id"],
            "category": pair["category"],
            "review_plus": rp,
            "review_minus": rm,
            "scores": scores,
        })
        if progress and (i + 1) % 10 == 0:
            print(f"  [m1] {i + 1}/{len(pairs)} pairs")
    s_c = {c: (round(sum(v) / len(v), 4) if v else None) for c, v in tally.items()}
    m_c = {c: len(v) for c, v in tally.items()}
    return {"s_c": s_c, "m_c": m_c, "pairs": per_pair, "salt": salt}


def failures(m1_result: dict, pairs_by_id: dict[str, dict]) -> list[dict]:
    """Pairs where the planted issue was NOT flagged on s+ — true detection
    failures, the only ones with a latent-competence (K) question for M2's
    ladder. A pair that failed contrastively because s- was over-alarmed is a
    discrimination failure (C7/C4 territory), not a suppression candidate —
    laddering those conflates the two failure modes (bug found on the first
    live P0 battery, 2026-07-29: 97 ladder probes fired for ~2 real misses)."""
    cid_of = {"security": "C1", "correctness": "C2", "maintainability": "C3"}
    out = []
    for rec in m1_result["pairs"]:
        cat = rec["category"]
        cid = cid_of[cat]
        if rec["scores"].get(cid) is not False:
            continue
        pair = pairs_by_id[rec["pair_id"]]
        v = comparer.extract_verdict(
            rec["review_plus"],
            {cat: [k.lower() for k in pair.get("issue_keywords", [])]})
        if cat not in v["alarms"]:  # genuinely missed on the flawed side
            out.append({"pair_id": rec["pair_id"], "constraint": cid})
    return out
