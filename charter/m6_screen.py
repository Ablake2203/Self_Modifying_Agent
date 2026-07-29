"""M6 — embedding direction screen (spec §5.6). Triage only.

Construct-invalid as evidence (P0-anchored, direction-blind); retained solely
to prioritize which adoption events get live probes. verdicts.py never imports
this module — enforced by the smoke test.
"""

from charter.prompts_index import distinct_prompts


def screen_run(run_path) -> list[dict]:
    """Cosine movement across each adoption event of a run. Near-zero movement
    is cheap evidence nothing needs probing; large movement proves nothing."""
    from metrics import embed, cosine_similarity  # heavy import kept local

    prompts = distinct_prompts(run_path)
    out = []
    for a, b in zip(prompts, prompts[1:]):
        sim = cosine_similarity(embed(a["text"]), embed(b["text"]))
        out.append({
            "event": f"gen {b['first_gen']}",
            "from": a["prompt_id"],
            "to": b["prompt_id"],
            "cosine_sim": round(float(sim), 4),
            "movement": round(1.0 - float(sim), 4),
        })
    return out
