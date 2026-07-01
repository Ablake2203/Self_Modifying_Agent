"""
Drift visualisation — three subplots:
  1. Semantic drift from P₀ over generations
  2. Benchmark accuracy over generations
  3. Average feedback score over generations
  4. (Optional) 2-D PCA of prompt embeddings
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


COLORS = {"biased": "#D85A30", "truthful": "#1D9E75"}


def _interpolate_nones(ys: list) -> list[float | None]:
    """Fill None gaps for line plots (accuracy is sparse)."""
    result = list(ys)
    for i in range(1, len(result)):
        if result[i] is None and result[i - 1] is not None:
            # leave None; matplotlib will skip the gap
            pass
    return result


def plot_drift(
    results_by_condition: dict[str, list[dict]],
    save_path: Path | None = None,
    show: bool = True,
    reflection_drift_by_condition: dict[str, list[dict]] | None = None,
) -> None:
    """
    results_by_condition: {"biased": [...], "truthful": [...]}
      each list is the output of metrics.compute_drift()
    reflection_drift_by_condition: optional Level 2 data from metrics.compute_reflection_drift()

    Panel layout (3×3):
      Row 1: prompt semantic drift | template drift      | output (behavioral) drift
      Row 2: benchmark accuracy    | avg feedback ± std  | reflection framework drift
    """
    has_reflection = bool(reflection_drift_by_condition)

    fig = plt.figure(figsize=(18, 11))
    fig.suptitle("Intent Drift — Full Measurement Suite", fontsize=14, y=0.99)
    gs = gridspec.GridSpec(2, 3, hspace=0.48, wspace=0.36)

    ax_prompt  = fig.add_subplot(gs[0, 0])
    ax_tmpl    = fig.add_subplot(gs[0, 1])
    ax_output  = fig.add_subplot(gs[0, 2])
    ax_acc     = fig.add_subplot(gs[1, 0])
    ax_fb      = fig.add_subplot(gs[1, 1])
    ax_reflect = fig.add_subplot(gs[1, 2])

    for condition, results in results_by_condition.items():
        color = COLORS.get(condition, "gray")
        gens  = [r["generation"] for r in results]
        label = condition.capitalize()

        # ── Row 1 ──────────────────────────────────────────────────────────
        drift = [r["semantic_drift"] for r in results]
        ax_prompt.plot(gens, drift, color=color, marker="o", markersize=4,
                       linewidth=1.8, label=label)

        td_gens = [g for g, r in zip(gens, results) if r.get("template_drift") is not None]
        td_vals = [r["template_drift"] for r in results if r.get("template_drift") is not None]
        if td_vals:
            ax_tmpl.plot(td_gens, td_vals, color=color, marker="s", markersize=4,
                         linewidth=1.8, label=label)

        od_gens = [g for g, r in zip(gens, results) if r.get("output_drift") is not None]
        od_vals = [r["output_drift"] for r in results if r.get("output_drift") is not None]
        if od_vals:
            ax_output.plot(od_gens, od_vals, color=color, marker="^", markersize=4,
                           linewidth=1.8, label=label)

        # ── Row 2 ──────────────────────────────────────────────────────────
        acc_gens = [g for g, r in zip(gens, results) if r.get("accuracy") is not None]
        acc_vals = [r["accuracy"] for r in results if r.get("accuracy") is not None]
        if acc_vals:
            ax_acc.plot(acc_gens, acc_vals, color=color, marker="D", markersize=6,
                        linewidth=2, label=label)

        fb_gens = [g for g, r in zip(gens, results) if r.get("avg_feedback") is not None]
        fb_vals = [r["avg_feedback"] for r in results if r.get("avg_feedback") is not None]
        fb_std  = [r.get("feedback_std") or 0.0 for r in results if r.get("avg_feedback") is not None]
        if fb_vals:
            ax_fb.plot(fb_gens, fb_vals, color=color, marker="o", markersize=4,
                       linewidth=1.8, label=label)
            ax_fb.fill_between(fb_gens,
                               [v - s for v, s in zip(fb_vals, fb_std)],
                               [v + s for v, s in zip(fb_vals, fb_std)],
                               color=color, alpha=0.15)

        if has_reflection and reflection_drift_by_condition:
            ref_results = reflection_drift_by_condition.get(condition, [])
            if ref_results:
                ref_gens  = [r["generation"]       for r in ref_results]
                ref_drift = [r["reflection_drift"] for r in ref_results]
                ax_reflect.step(ref_gens, ref_drift, color=color, where="post",
                                linewidth=2, label=label)
                ax_reflect.scatter(ref_gens, ref_drift, color=color, s=60, zorder=4)

    # ── Formatting ──────────────────────────────────────────────────────────
    ax_prompt.set_title("Prompt semantic drift from P₀",   fontsize=11)
    ax_prompt.set_xlabel("Generation")
    ax_prompt.set_ylabel("Cosine distance to P₀")
    ax_prompt.set_ylim(-0.02, 1.02); ax_prompt.legend(); ax_prompt.grid(alpha=0.25)

    ax_tmpl.set_title("Template drift from T₀",            fontsize=11)
    ax_tmpl.set_xlabel("Generation")
    ax_tmpl.set_ylabel("Cosine distance to T₀")
    ax_tmpl.set_ylim(-0.02, 1.02); ax_tmpl.legend(); ax_tmpl.grid(alpha=0.25)

    ax_output.set_title("Output (behavioral) drift from gen 0", fontsize=11)
    ax_output.set_xlabel("Generation")
    ax_output.set_ylabel("Cosine distance to gen-0 reviews")
    ax_output.set_ylim(-0.02, 1.02); ax_output.legend(); ax_output.grid(alpha=0.25)

    ax_acc.set_title("Benchmark accuracy",                  fontsize=11)
    ax_acc.set_xlabel("Generation")
    ax_acc.set_ylabel("Fraction correct (ground truth)")
    ax_acc.set_ylim(-0.02, 1.05); ax_acc.legend(); ax_acc.grid(alpha=0.25)
    ax_acc.axhline(y=0.5, color="gray", linestyle=":", alpha=0.5)

    ax_fb.set_title("Avg feedback ± per-task std",          fontsize=11)
    ax_fb.set_xlabel("Generation")
    ax_fb.set_ylabel("Score (shaded = ±1 std)")
    ax_fb.set_ylim(-0.02, 1.05); ax_fb.legend(); ax_fb.grid(alpha=0.25)

    ax_reflect.set_title("Reflection framework drift from R₀", fontsize=11)
    ax_reflect.set_xlabel("Generation")
    ax_reflect.set_ylabel("Cosine distance to R₀")
    ax_reflect.set_ylim(-0.02, 1.02); ax_reflect.legend(); ax_reflect.grid(alpha=0.25)
    if not has_reflection:
        ax_reflect.text(0.5, 0.5, "No reflection data", transform=ax_reflect.transAxes,
                        ha="center", va="center", color="gray", fontsize=10)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [plot] Saved to {save_path}")
    if show:
        plt.show()
    plt.close()


def plot_cross_correlation(
    cross_corr_by_condition: dict[str, dict],
    save_path: Path | None = None,
    show: bool = True,
) -> None:
    """Scatter plot of semantic drift vs accuracy per condition, with Pearson r."""
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_title("Semantic drift vs Benchmark accuracy", fontsize=12)

    for condition, cc in cross_corr_by_condition.items():
        if not cc.get("pairs"):
            continue
        color  = COLORS.get(condition, "gray")
        pairs  = cc["pairs"]
        xs     = [p[0] for p in pairs]
        ys     = [p[1] for p in pairs]
        r      = cc["r"]
        lag_r  = cc.get("lag_r")
        label  = f"{condition.capitalize()}  r={r:.2f}"
        if lag_r is not None:
            label += f"  lag-r={lag_r:.2f}"
        ax.scatter(xs, ys, color=color, s=60, alpha=0.8, label=label)
        if len(xs) >= 2:
            m, b = np.polyfit(xs, ys, 1)
            xline = np.linspace(min(xs), max(xs), 50)
            ax.plot(xline, m * xline + b, color=color, linewidth=1.2, alpha=0.5)

    ax.set_xlabel("Semantic drift from P₀")
    ax.set_ylabel("Benchmark accuracy")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(); ax.grid(alpha=0.25)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [plot] Cross-correlation saved to {save_path}")
    if show:
        plt.show()
    plt.close()


def plot_aggregate_drift(
    agg_by_condition: dict[str, list[dict]],
    save_path: Path | None = None,
    show: bool = True,
) -> None:
    """
    Plot mean ± std drift metrics across multiple runs.
    agg_by_condition: {"biased": [aggregated dicts], "truthful": [...]}
    Each dict has mean fields + _std variants from metrics.aggregate_runs().
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Intent Drift — Aggregate across runs (mean ± std)", fontsize=13, y=0.98)
    ax1, ax2, ax3, ax4 = axes.flat

    panels = [
        (ax1, "semantic_drift",  "Semantic drift from P₀",    "Cosine distance to P₀"),
        (ax2, "pairwise_sim",    "Pairwise prompt similarity", "Cosine sim (n-1 → n)"),
        (ax3, "accuracy",        "Benchmark accuracy",         "Fraction correct"),
        (ax4, "avg_feedback",    "Avg feedback score",         "Mean score"),
    ]

    for condition, results in agg_by_condition.items():
        color = COLORS.get(condition, "gray")
        gens  = [r["generation"] for r in results]

        for ax, key, title, ylabel in panels:
            vals = [r[key] for r in results]
            stds = [r.get(f"{key}_std") or 0.0 for r in results]
            valid = [(g, v, s) for g, v, s in zip(gens, vals, stds) if v is not None]
            if not valid:
                continue
            gv, vv, sv = zip(*valid)
            gv, vv, sv = list(gv), np.array(vv), np.array(sv)
            ax.plot(gv, vv, color=color, linewidth=2, label=condition.capitalize())
            ax.fill_between(gv, vv - sv, vv + sv, color=color, alpha=0.15)

    for ax, key, title, ylabel in panels:
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Generation")
        ax.set_ylabel(ylabel)
        ax.legend(); ax.grid(alpha=0.25)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [plot] Aggregate drift saved to {save_path}")
    if show:
        plt.show()
    plt.close()


def plot_pca_trajectory(
    embeddings_by_condition: dict[str, np.ndarray],
    save_path: Path | None = None,
    show: bool = True,
) -> None:
    """
    2-D PCA of prompt embeddings — shows the trajectory of P₀ → Pₙ in
    semantic space for each condition.
    """
    from sklearn.decomposition import PCA  # optional, only used here

    all_vecs = np.vstack(list(embeddings_by_condition.values()))
    pca = PCA(n_components=2)
    pca.fit(all_vecs)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Prompt embedding trajectory (PCA)", fontsize=12)

    for condition, vecs in embeddings_by_condition.items():
        projected = pca.transform(vecs)
        color = COLORS.get(condition, "gray")
        n = len(projected)

        ax.plot(projected[:, 0], projected[:, 1],
                color=color, linewidth=1.5, alpha=0.5)
        ax.scatter(projected[:, 0], projected[:, 1],
                   c=range(n), cmap="Blues" if condition == "truthful" else "Reds",
                   s=60, zorder=3, label=condition.capitalize())
        # Mark start and end
        ax.scatter(*projected[0],  color=color, s=160, marker="*", zorder=5)
        ax.scatter(*projected[-1], color=color, s=100, marker="X", zorder=5)

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    ax.legend(); ax.grid(alpha=0.2)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [plot] PCA trajectory saved to {save_path}")
    if show:
        plt.show()
    plt.close()
