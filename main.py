"""
Entry point.

Quick test (3 generations, no benchmark eval overhead):
    python main.py --condition biased --generations 3 --no-eval

Full biased experiment:
    python main.py --condition biased

Control experiment:
    python main.py --condition truthful

Ablation baseline (frozen — no self-modification):
    python main.py --condition baseline

All three conditions back to back:
    python main.py --all

Both conditions back to back (biased + truthful):
    python main.py --both

Plot from existing store files:
    python main.py --plot runs/biased_*.json runs/truthful_*.json runs/baseline_*.json
"""

import argparse
import json
import sys
from pathlib import Path

import config


def run(condition: str, generations: int, no_eval: bool) -> Path:
    # Patch config if overridden on CLI
    config.NUM_GENERATIONS = generations
    if no_eval:
        config.BENCHMARK_EVAL_EVERY = generations + 999  # effectively never

    from evolution import run_experiment
    return run_experiment(condition)


def plot_from_files(paths: list[str]) -> None:
    from metrics import (compute_drift, compute_reflection_drift,
                         compute_cross_correlation, embedding_matrix, print_summary)
    from visualize import plot_drift, plot_pca_trajectory, plot_cross_correlation
    import config as cfg

    results_by_condition:            dict[str, list[dict]] = {}
    reflection_drift_by_condition:   dict[str, list[dict]] = {}
    cross_corr_by_condition:         dict[str, dict]       = {}
    embeddings_by_condition:         dict = {}

    for p in paths:
        store     = json.loads(Path(p).read_text())
        condition = store[0].get("condition", Path(p).stem.split("_")[0])
        drift     = compute_drift(store)
        results_by_condition[condition] = drift
        print_summary(drift)

        ref_drift = compute_reflection_drift(store)
        if ref_drift:
            reflection_drift_by_condition[condition] = ref_drift

        cc = compute_cross_correlation(drift)
        cross_corr_by_condition[condition] = cc
        if cc["r"] is not None:
            lag_str = f"  lag-r={cc['lag_r']:.3f}" if cc["lag_r"] is not None else ""
            print(f"  [{condition}] drift-vs-accuracy  r={cc['r']:.3f}  p={cc['p']:.3f}{lag_str}  (n={cc['n']})")

        try:
            embeddings_by_condition[condition] = embedding_matrix(store)
        except Exception:
            pass

    out_drift = cfg.RUNS_DIR / "drift_analysis.png"
    plot_drift(
        results_by_condition,
        save_path=out_drift,
        show=True,
        reflection_drift_by_condition=reflection_drift_by_condition or None,
    )

    if any(cc.get("pairs") for cc in cross_corr_by_condition.values()):
        out_cc = cfg.RUNS_DIR / "cross_correlation.png"
        plot_cross_correlation(cross_corr_by_condition, save_path=out_cc, show=True)

    if len(embeddings_by_condition) >= 1:
        try:
            out_pca = cfg.RUNS_DIR / "pca_trajectory.png"
            plot_pca_trajectory(embeddings_by_condition, save_path=out_pca, show=True)
        except ImportError:
            print("  [info] sklearn not installed — skipping PCA plot.")


def plot_aggregate_from_files(paths_by_condition: dict[str, list[str]]) -> None:
    from metrics import compute_drift, aggregate_runs
    from visualize import plot_aggregate_drift
    import config as cfg

    agg_by_condition: dict[str, list[dict]] = {}

    for condition, paths in paths_by_condition.items():
        all_drift = []
        for p in paths:
            store = json.loads(Path(p).read_text())
            all_drift.append(compute_drift(store))
        agg_by_condition[condition] = aggregate_runs(all_drift)
        print(f"  [{condition}] aggregated {len(paths)} runs")

    out = cfg.RUNS_DIR / "aggregate_drift.png"
    plot_aggregate_drift(agg_by_condition, save_path=out, show=True)


def check_backend() -> bool:
    print(f"\n  Checking LLM backend ({config.LLM_BACKEND})...")
    from llm import check_backend as _check
    ok = _check()
    if ok:
        print("  Backend reachable.\n")
    else:
        print("\n  ERROR: Cannot reach LLM backend.")
        if config.LLM_BACKEND == "ollama":
            print("  Make sure Ollama is running:  ollama serve")
            print(f"  And the model is pulled:      ollama pull {config.OLLAMA_MODEL}")
        else:
            print("  Check your OPENAI_API_KEY and OPENAI_BASE_URL env vars.")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Intent Drift — Prompt Evolution Experiment"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--condition", choices=["biased", "truthful", "baseline"],
        help="Run one experiment condition",
    )
    group.add_argument(
        "--both", action="store_true",
        help="Run biased then truthful back-to-back",
    )
    group.add_argument(
        "--all", action="store_true",
        help="Run all three conditions: biased, truthful, baseline (ablation)",
    )
    group.add_argument(
        "--plot", nargs="+", metavar="STORE_JSON",
        help="Plot drift from existing store files (skip running)",
    )
    parser.add_argument(
        "--generations", type=int, default=config.NUM_GENERATIONS,
        help=f"Number of generations (default: {config.NUM_GENERATIONS})",
    )
    parser.add_argument(
        "--no-eval", action="store_true",
        help="Skip benchmark eval (faster, for quick tests)",
    )
    parser.add_argument(
        "--runs", type=int, default=1,
        help="Number of independent runs per condition (seeds: RANDOM_SEED, +1, +2, ...)",
    )

    args = parser.parse_args()

    if args.plot:
        plot_from_files(args.plot)
        return

    if not check_backend():
        sys.exit(1)

    if args.all:
        conditions = ["biased", "truthful", "baseline"]
    elif args.both:
        conditions = ["biased", "truthful"]
    else:
        conditions = [args.condition]
    paths_by_condition: dict[str, list[str]] = {c: [] for c in conditions}

    base_seed = config.RANDOM_SEED if config.RANDOM_SEED is not None else 42

    import snapshot
    snapshot.save()  # freeze state-0 once before anything runs

    for run_idx in range(args.runs):
        config.RANDOM_SEED = base_seed + run_idx
        if args.runs > 1:
            print(f"\n{'='*60}")
            print(f"  Run {run_idx + 1}/{args.runs}  (seed={config.RANDOM_SEED})")
        for cond_idx, cond in enumerate(conditions):
            snapshot.restore()  # every condition starts from identical state-0
            p = run(cond, args.generations, args.no_eval)
            snapshot.save_evolved(cond, config.RANDOM_SEED)  # preserve what this condition evolved
            paths_by_condition[cond].append(str(p))

    all_paths = [p for paths in paths_by_condition.values() for p in paths]
    print("\nGenerating drift plots...")

    if args.runs > 1:
        plot_aggregate_from_files(paths_by_condition)
    else:
        plot_from_files(all_paths)


if __name__ == "__main__":
    main()
