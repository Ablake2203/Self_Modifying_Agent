"""
Live smoke test for drift_eval.py: gen 0 vs gen 20 of biased_20260716_163550
(branch A). Small dataset (n=4 -> ~5 examples) to keep API calls cheap while
still exercising every code path once.
"""
import json
import time

import drift_eval as de

with open("runs/biased_20260716_163550_branchA.json") as f:
    store = json.load(f)

prompt_0  = store[0]["prompt"]
prompt_20 = store[20]["prompt"]

small_dataset = de._build_probe_dataset(n=4, seed=42)
print(f"Smoke dataset: {len(small_dataset)} examples "
      f"({sum(1 for e in small_dataset if e.task['has_issue'])} issue / "
      f"{sum(1 for e in small_dataset if not e.task['has_issue'])} clean)")

t0 = time.time()
print("\n=== Running experiment: generation 0 ===")
exp_0 = de.run_experiment(prompt_0, generation=0, dataset=small_dataset)
print("gen 0 scores:", json.dumps(exp_0.scores, indent=2))

print("\n=== Running experiment: generation 20 ===")
exp_20 = de.run_experiment(prompt_20, generation=20, prompt_0=prompt_0, dataset=small_dataset)
print("gen 20 scores:", json.dumps(exp_20.scores, indent=2))

report = de.compare_experiments(baseline=exp_0, candidate=exp_20)
print("\n=== Comparison report ===")
print(json.dumps(report, indent=2))
print(f"\nElapsed: {time.time() - t0:.1f}s")
