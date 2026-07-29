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


def failures(m1_result: dict) -> list[dict]:
    """(pair_id, constraint) list where an obligation to *flag* failed —
    these are what M2's ladder climbs. Only detection constraints (C1-C3)
    have a latent-competence question; C4/C6/C7 are style/honesty."""
    out = []
    for rec in m1_result["pairs"]:
        for cid in ("C1", "C2", "C3"):
            if rec["scores"].get(cid) is False:
                out.append({"pair_id": rec["pair_id"], "constraint": cid})
    return out
