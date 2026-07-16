"""
Measure the noise floor of the candidate-adoption gate.

Answers: "If I evaluate the SAME prompt (P0) twice via eval_on_validation,
how different do the two scores look?" — that spread is what the adoption
gate currently mistakes for candidate improvement.

Two variance sources are measured separately:
  1. Full-pipeline noise  — R independent evaluations of P0 on the 8
     validation tasks (fresh reviews each time, temp 0.7 agent + judge).
     The stdev of the 8-task average is sigma_null.
  2. Judge-only noise     — the reviews from rep 1 are re-scored J extra
     times each. Isolates judge nondeterminism from review-generation
     variance.

The gate compares two independent evaluations (candidate vs parent), so the
null spread of that *difference* is sigma_delta = sqrt(2) * sigma_null.
A margin gate should require candidate - parent > ~1.5 * sigma_delta.

Usage:
    python measure_noise.py --condition truthful --reps 10 --judge-reps 3
    python measure_noise.py --condition both --reps 10

Cost per rep: 8 agent calls + 8 judge calls. Judge-reps add 8*J judge calls
(once, on rep-1 reviews). Results are saved incrementally after every rep,
so a rate-limit death loses nothing.
"""

import argparse
import json
import statistics
import time
from datetime import datetime
from itertools import combinations
from pathlib import Path

import config
from benchmark import VALIDATION_TASKS
from evolution import P0, T0, get_review
from feedback import score_review


def run_reps(condition: str, reps: int, out: dict, out_path: Path,
             temperature: float | None = None,
             task_filter: list[str] | None = None) -> list[dict]:
    """R independent full evaluations of P0 on validation tasks (optionally a subset)."""
    eval_tasks = ([t for t in VALIDATION_TASKS if t["id"] in task_filter]
                  if task_filter else VALIDATION_TASKS)
    rep_results = out["conditions"].setdefault(condition, {}).setdefault("reps", [])
    start = len(rep_results)  # resume-friendly if re-run with same out file
    for i in range(start, reps):
        print(f"  [{condition}] rep {i + 1}/{reps}: reviewing {len(eval_tasks)} tasks...")
        tasks = []
        for task in eval_tasks:
            review = get_review(P0, task["code"], T0, temperature=temperature)
            fb = score_review(review, task, condition)
            tasks.append({
                "task_id": task["id"],
                "review":  review,
                "score":   fb["score"],
                "reason":  fb["reason"],
            })
        avg = sum(t["score"] for t in tasks) / len(tasks)
        rep_results.append({"avg": avg, "tasks": tasks})
        print(f"  [{condition}] rep {i + 1}/{reps}: avg = {avg:.3f}")
        _save(out, out_path)
    return rep_results


def run_judge_reps(condition: str, judge_reps: int, out: dict, out_path: Path) -> None:
    """Re-score rep-1 reviews J extra times each — judge-only variance."""
    cond = out["conditions"][condition]
    if judge_reps <= 0 or not cond.get("reps"):
        return
    rescores = cond.setdefault("judge_rescores", {})  # task_id -> [scores]
    base_tasks = cond["reps"][0]["tasks"]
    task_by_id = {t["id"]: t for t in VALIDATION_TASKS}
    for t in base_tasks:
        scores = rescores.setdefault(t["task_id"], [t["score"]])
        while len(scores) < judge_reps + 1:
            fb = score_review(t["review"], task_by_id[t["task_id"]], condition)
            scores.append(fb["score"])
            _save(out, out_path)
    print(f"  [{condition}] judge-only rescoring done ({judge_reps} extra scores per review).")


def summarize(condition: str, out: dict) -> dict:
    cond = out["conditions"][condition]
    avgs = [r["avg"] for r in cond["reps"]]
    n = len(avgs)
    summary: dict = {"n_reps": n, "avgs": [round(a, 4) for a in avgs]}

    if n >= 2:
        sigma_null = statistics.stdev(avgs)
        deltas = [abs(a - b) for a, b in combinations(avgs, 2)]
        summary.update({
            "mean":                 round(statistics.mean(avgs), 4),
            "sigma_null":           round(sigma_null, 4),
            "sigma_delta_theory":   round(sigma_null * 2 ** 0.5, 4),
            "mean_abs_pairwise_delta": round(statistics.mean(deltas), 4),
            "max_pairwise_delta":   round(max(deltas), 4),
            "suggested_adopt_margin": round(1.5 * sigma_null * 2 ** 0.5, 4),
        })

    rescores = cond.get("judge_rescores")
    if rescores and any(len(s) >= 2 for s in rescores.values()):
        per_review_var = [
            statistics.variance(s) for s in rescores.values() if len(s) >= 2
        ]
        judge_var_of_avg = sum(per_review_var) / (len(per_review_var) ** 2)
        summary["judge_only_sigma_of_avg"] = round(judge_var_of_avg ** 0.5, 4)
        summary["judge_reviews_with_any_flip"] = sum(
            1 for s in rescores.values() if len(set(s)) > 1
        )
        summary["judge_reviews_rescored"] = len(per_review_var)

    cond["summary"] = summary
    return summary


def print_summary(condition: str, s: dict) -> None:
    print(f"\n  ── {condition} ──")
    print(f"  evals of identical prompt P0:  {s['avgs']}")
    if "sigma_null" not in s:
        print("  (need >= 2 reps for statistics)")
        return
    print(f"  mean score:                    {s['mean']:.3f}")
    print(f"  sigma_null (one eval):         {s['sigma_null']:.3f}")
    print(f"  sigma_delta (gate comparison): {s['sigma_delta_theory']:.3f}")
    print(f"  mean |delta| between evals:    {s['mean_abs_pairwise_delta']:.3f}")
    print(f"  max  |delta| between evals:    {s['max_pairwise_delta']:.3f}")
    print(f"  --> suggested ADOPT_MARGIN:    {s['suggested_adopt_margin']:.3f}")
    if "judge_only_sigma_of_avg" in s:
        judge = s["judge_only_sigma_of_avg"]
        total = s["sigma_null"]
        print(f"  judge-only sigma of avg:       {judge:.3f}"
              f"  ({s['judge_reviews_with_any_flip']}/{s['judge_reviews_rescored']}"
              f" reviews got a different score on re-judge)")
        if total > 0:
            share = min(1.0, (judge / total) ** 2)
            print(f"  variance share: judge {share:.0%} / review-generation {1 - share:.0%}")
    print(
        "  Interpretation: the old gate adopted any candidate whose eval beat the\n"
        "  parent's by > 0. Two evals of the SAME prompt differ by "
        f"{s['mean_abs_pairwise_delta']:.3f} on average\n"
        "  — any adoption below the suggested margin is indistinguishable from noise."
    )


def _save(out: dict, out_path: Path) -> None:
    out_path.write_text(json.dumps(out, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure adoption-gate noise floor (sigma_null)")
    parser.add_argument("--condition", choices=["biased", "truthful", "both"], default="truthful")
    parser.add_argument("--reps", type=int, default=10,
                        help="independent full evaluations of P0 (default 10)")
    parser.add_argument("--judge-reps", type=int, default=3,
                        help="extra judge re-scores of rep-1 reviews (default 3, 0 to skip)")
    parser.add_argument("--out", type=str, default=None,
                        help="output JSON (default runs/noise_null_<ts>.json); pass an existing file to resume")
    parser.add_argument("--temperature", type=float, default=None,
                        help="review-generation temperature (default: config.LLM_TEMPERATURE; "
                             "use config.VALIDATION_TEMPERATURE to measure the gate's noise)")
    parser.add_argument("--tasks", type=str, default=None,
                        help="comma-separated task ids — flip-test only these tasks "
                             "(e.g. after editing the validation set)")
    args = parser.parse_args()

    task_filter = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
    if task_filter:
        known = {t["id"] for t in VALIDATION_TASKS}
        unknown = [t for t in task_filter if t not in known]
        if unknown:
            raise SystemExit(f"Unknown task ids: {unknown}. Known: {sorted(known)}")

    conditions = ["biased", "truthful"] if args.condition == "both" else [args.condition]

    out_path = Path(args.out) if args.out else (
        config.RUNS_DIR / f"noise_null_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    if args.out and out_path.exists():
        out = json.loads(out_path.read_text())
        print(f"Resuming from {out_path}")
    else:
        out = {
            "created":     datetime.now().isoformat(timespec="seconds"),
            "agent_model": config.OPENAI_MODEL,
            "judge_model": config.JUDGE_MODEL,
            "temperature": args.temperature if args.temperature is not None else config.LLM_TEMPERATURE,
            "n_tasks":     len(VALIDATION_TASKS),
            "conditions":  {},
        }

    n_agent = args.reps * len(VALIDATION_TASKS) * len(conditions)
    n_judge = (args.reps + args.judge_reps) * len(VALIDATION_TASKS) * len(conditions)
    print(f"Cost: ~{n_agent} agent calls + ~{n_judge} judge calls total. Output: {out_path}\n")

    t0 = time.time()
    for cond in conditions:
        run_reps(cond, args.reps, out, out_path, temperature=args.temperature,
                 task_filter=task_filter)
        run_judge_reps(cond, args.judge_reps, out, out_path)
        print_summary(cond, summarize(cond, out))
        _save(out, out_path)

    print(f"\nDone in {time.time() - t0:.0f}s. Full data: {out_path}")


if __name__ == "__main__":
    main()
