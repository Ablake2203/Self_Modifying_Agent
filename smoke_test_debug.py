"""Debug pass: isolate out-of-role recall and inspect raw reviews/verdicts."""
import json
import drift_eval as de

with open("runs/biased_20260716_163550_branchA.json") as f:
    store = json.load(f)

prompt_0  = store[0]["prompt"]
prompt_20 = store[20]["prompt"]
small_dataset = de._build_probe_dataset(n=4, seed=42)

print("--- out-of-role capability probe, per example ---")
for e in small_dataset:
    if not e.task["has_issue"]:
        continue
    hit = de._capability_probe(e)
    print(f"  {e.task['id']} ({e.issue_type}): capability_probe -> {hit}")

print("\n--- in-role review, gen 0, per issue example ---")
for e in small_dataset:
    if not e.task["has_issue"]:
        continue
    review = de.get_review(prompt_0, e.task["code"])
    hit = de.issue_detected(review.lower(), e.task)
    print(f"  {e.task['id']}: issue_detected={hit}")
    print(f"    review[:200] = {review[:200]!r}")

print("\n--- in-role review, gen 20, per issue example ---")
for e in small_dataset:
    if not e.task["has_issue"]:
        continue
    review = de.get_review(prompt_20, e.task["code"])
    hit = de.issue_detected(review.lower(), e.task)
    print(f"  {e.task['id']}: issue_detected={hit}")
    print(f"    review[:200] = {review[:200]!r}")

print("\n--- gen 0 precision check (all examples) ---")
for e in small_dataset:
    review = de.get_review(prompt_0, e.task["code"])
    fa = de.raises_false_alarm(review)
    print(f"  {e.task['id']} (has_issue={e.task['has_issue']}): false_alarm={fa}")
    print(f"    review[:200] = {review[:200]!r}")
