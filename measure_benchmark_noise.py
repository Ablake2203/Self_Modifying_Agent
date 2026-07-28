"""
Measure the benchmark channel's noise floor: run eval_benchmark on the SAME
prompt repeatedly and report the accuracy spread. The spread is the minimum
difference between two benchmark readings that can be interpreted as real.

Uses agent (Mistral) calls only — benchmark scoring is keyword-based, no
judge quota is spent. Rerun after any change to BENCHMARK_TEMPERATURE,
BENCHMARK_TASKS, or the agent model.

Usage:
    python measure_benchmark_noise.py --reps 3
    python measure_benchmark_noise.py --reps 3 --prompt-from runs/x.json --gen 20
"""

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

import config
from evolution import P0, eval_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure benchmark accuracy noise floor")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--prompt-from", type=str, default=None,
                        help="run JSON to take the prompt from (default: P0)")
    parser.add_argument("--gen", type=int, default=None,
                        help="generation whose prompt to use (with --prompt-from)")
    parser.add_argument("--out", type=str, default="runs/noise_benchmark_p0.json")
    parser.add_argument("--temperature", type=float, default=None,
                        help="override config.BENCHMARK_TEMPERATURE for this measurement")
    args = parser.parse_args()
    if args.temperature is not None:
        config.BENCHMARK_TEMPERATURE = args.temperature

    prompt, label = P0, "P0"
    if args.prompt_from:
        entries = json.loads(Path(args.prompt_from).read_text())
        entry   = next(e for e in entries if e["generation"] == (args.gen if args.gen is not None else entries[-1]["generation"]))
        prompt, label = entry["prompt"], f"{Path(args.prompt_from).stem}:gen{entry['generation']}"

    out_path = Path(args.out)
    out = json.loads(out_path.read_text()) if out_path.exists() else {
        "created": datetime.now().isoformat(timespec="seconds"),
        "agent_model": config.OPENAI_MODEL,
        "benchmark_temperature": config.BENCHMARK_TEMPERATURE,
        "prompt_label": label,
        "reps": [],
    }

    print(f"Benchmark noise floor: {args.reps} reps × {len(__import__('benchmark').BENCHMARK_TASKS)} tasks, "
          f"prompt={label}, temp={config.BENCHMARK_TEMPERATURE}")
    for i in range(len(out["reps"]), args.reps):
        acc, breakdown = eval_benchmark(prompt, return_breakdown=True)
        out["reps"].append({"accuracy": acc, "breakdown": breakdown})
        out_path.write_text(json.dumps(out, indent=2))
        print(f"  rep {i + 1}/{args.reps}: {acc:.2%}  {breakdown}")

    accs = [r["accuracy"] for r in out["reps"]]
    if len(accs) >= 2:
        print(f"\n  accuracies: {[f'{a:.2%}' for a in accs]}")
        print(f"  spread (max-min): {max(accs) - min(accs):.2%}")
        print(f"  stdev:            {statistics.stdev(accs):.4f}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    main()
