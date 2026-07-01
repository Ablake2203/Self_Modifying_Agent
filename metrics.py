"""
Drift measurement:

  Semantic drift  — cosine distance between each Pₙ and P₀ in embedding space.
                    Uses sentence-transformers (CPU, no GPU, no API).

  Behavioral drift — ground-truth accuracy on fixed benchmark over generations.

  Feedback drift   — average feedback score over generations (proxy for
                     how well the agent has "learned" the biased reward).
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cosine as cosine_dist

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        import config
        print("  [metrics] Loading embedding model (first time, may take ~30s)...")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        print("  [metrics] Embedding model ready.")
    return _model


def embed(text: str) -> np.ndarray:
    return _get_model().encode(text, convert_to_numpy=True)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    return float(1.0 - cosine_dist(v1, v2))


def _avg_review_embedding(entry: dict) -> np.ndarray | None:
    """Mean embedding of all reviews produced in a generation (truncated for speed)."""
    reviews = [t["review"] for t in entry.get("task_results", []) if t.get("review")]
    if not reviews:
        return None
    vecs = [embed(r[:500]) for r in reviews]
    return np.mean(vecs, axis=0)


def compute_drift(store: list[dict]) -> list[dict]:
    """
    For each generation entry in the store, compute:
      - semantic_drift  : cosine distance from P₀ prompt embedding
      - pairwise_sim    : cosine sim to previous generation's prompt
      - template_drift  : cosine distance from T₀ template embedding
      - output_drift    : cosine distance from gen-0 mean review embedding (behavioral layer)
      - feedback_std    : std of per-task scores this generation (hidden oscillation)
      - accuracy        : benchmark accuracy (None if not evaluated that gen)
      - avg_feedback    : mean feedback score this generation
    """
    print("  [metrics] Embedding prompts, templates, and outputs...")
    prompt_vecs   = [embed(e["prompt"])                  for e in store]
    template_vecs = [embed(e["template"]) if e.get("template") else None for e in store]
    output_vecs   = [_avg_review_embedding(e)            for e in store]

    p0_vec = prompt_vecs[0]
    t0_vec = template_vecs[0]
    # Gen 0 has no reviews (baseline eval only) — anchor output drift to first gen with reviews
    o0_vec = next((v for v in output_vecs if v is not None), None)

    results = []
    for i, entry in enumerate(store):
        p_vec = prompt_vecs[i]
        t_vec = template_vecs[i]
        o_vec = output_vecs[i]

        sim_to_p0   = cosine_similarity(p0_vec, p_vec)
        sim_to_prev = cosine_similarity(prompt_vecs[i - 1], p_vec) if i > 0 else 1.0

        template_drift = (
            round(1.0 - cosine_similarity(t0_vec, t_vec), 4)
            if t_vec is not None and t0_vec is not None else None
        )
        output_drift = (
            round(1.0 - cosine_similarity(o0_vec, o_vec), 4)
            if o_vec is not None and o0_vec is not None else None
        )

        scores = [t["score"] for t in entry.get("task_results", []) if t.get("score") is not None]
        feedback_std = round(float(np.std(scores)), 4) if len(scores) >= 2 else None

        results.append({
            "generation":     entry["generation"],
            "condition":      entry.get("condition", "unknown"),
            "cosine_sim_p0":  round(sim_to_p0, 4),
            "semantic_drift": round(1.0 - sim_to_p0, 4),
            "pairwise_sim":   round(sim_to_prev, 4),
            "template_drift": template_drift,
            "output_drift":   output_drift,
            "feedback_std":   feedback_std,
            "accuracy":       entry.get("accuracy"),
            "avg_feedback":   entry.get("avg_feedback"),
        })

    return results


def embedding_matrix(store: list[dict]) -> np.ndarray:
    """Return (N_generations × embedding_dim) matrix of prompt embeddings — useful for PCA."""
    return np.vstack([embed(e["prompt"]) for e in store])


def compute_reflection_drift(store: list[dict]) -> list[dict]:
    """
    Track how far the reflection framework (DARA) has drifted from R₀.
    Only includes generations where the reflection field is present and changed.
    Returns list of {generation, reflection_drift}.
    """
    entries = [(e["generation"], e["reflection"]) for e in store if e.get("reflection")]
    if not entries:
        return []

    texts      = [t for _, t in entries]
    embeddings = [embed(t) for t in texts]
    r0_vec     = embeddings[0]

    results = []
    for (gen, _), vec in zip(entries, embeddings):
        sim = cosine_similarity(r0_vec, vec)
        results.append({
            "generation":       gen,
            "reflection_drift": round(1.0 - sim, 4),
        })
    return results


def compute_cross_correlation(drift_results: list[dict]) -> dict:
    """
    Pearson correlation between semantic drift and benchmark accuracy.
    Only uses generations where accuracy is available.
    Also computes lagged correlation: drift at gen N vs accuracy at gen N+lag.
    Returns dict with 'r', 'p', 'n', 'lag_r' (lag=1 step ahead).
    """
    from scipy.stats import pearsonr

    pairs = [(r["semantic_drift"], r["accuracy"])
             for r in drift_results if r["accuracy"] is not None]
    if len(pairs) < 3:
        return {"r": None, "p": None, "n": len(pairs), "lag_r": None}

    drifts   = [p[0] for p in pairs]
    accuracy = [p[1] for p in pairs]
    r, p     = pearsonr(drifts, accuracy)

    # Lag correlation: drift at step i predicts accuracy at step i+1
    lag_r = None
    if len(pairs) >= 4:
        lag_r, _ = pearsonr(drifts[:-1], accuracy[1:])

    return {
        "r":     round(float(r), 4),
        "p":     round(float(p), 4),
        "n":     len(pairs),
        "lag_r": round(float(lag_r), 4) if lag_r is not None else None,
        "pairs": list(zip(drifts, accuracy)),
    }


def aggregate_runs(all_drift_results: list[list[dict]]) -> list[dict]:
    """
    Aggregate drift metrics across multiple runs.
    Returns list of dicts with mean and std fields per generation.
    Assumes all runs have the same number of generations.
    """
    if not all_drift_results:
        return []

    n_gens = len(all_drift_results[0])
    aggregated = []

    for i in range(n_gens):
        gen = all_drift_results[0][i]["generation"]
        condition = all_drift_results[0][i].get("condition", "unknown")

        def mean_std(key):
            vals = [r[i][key] for r in all_drift_results if r[i][key] is not None]
            if not vals:
                return None, None
            return float(np.mean(vals)), float(np.std(vals))

        sd_mean,  sd_std  = mean_std("semantic_drift")
        ps_mean,  ps_std  = mean_std("pairwise_sim")
        td_mean,  td_std  = mean_std("template_drift")
        od_mean,  od_std  = mean_std("output_drift")
        fstd_mean, _      = mean_std("feedback_std")
        acc_mean, acc_std = mean_std("accuracy")
        fb_mean,  fb_std  = mean_std("avg_feedback")

        aggregated.append({
            "generation":          gen,
            "condition":           condition,
            "semantic_drift":      sd_mean,
            "semantic_drift_std":  sd_std,
            "pairwise_sim":        ps_mean,
            "pairwise_sim_std":    ps_std,
            "template_drift":      td_mean,
            "template_drift_std":  td_std,
            "output_drift":        od_mean,
            "output_drift_std":    od_std,
            "feedback_std":        fstd_mean,
            "accuracy":            acc_mean,
            "accuracy_std":        acc_std,
            "avg_feedback":        fb_mean,
            "avg_feedback_std":    fb_std,
        })

    return aggregated


def print_summary(drift_results: list[dict]) -> None:
    print(f"\n  {'Gen':>4}  {'Sem. Drift':>10}  {'Accuracy':>10}  {'Avg Feedback':>12}")
    print("  " + "-" * 44)
    for r in drift_results:
        acc  = f"{r['accuracy']:.2%}"    if r["accuracy"]    is not None else "    —"
        fb   = f"{r['avg_feedback']:.3f}" if r["avg_feedback"] is not None else "   —"
        print(f"  {r['generation']:>4}  {r['semantic_drift']:>10.4f}  {acc:>10}  {fb:>12}")
