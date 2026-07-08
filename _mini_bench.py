"""
Standalone validation script — run as subprocess after a code swap.
Imports all modules fresh (no cache), runs N tasks, prints average score.

Usage: python _mini_bench.py <condition> <n_tasks> <seed>
"""
import sys
import random

condition = sys.argv[1]
n_tasks   = int(sys.argv[2])
seed      = int(sys.argv[3])

random.seed(seed)

from benchmark import TASKS
from feedback import score_review
from evolution import get_review, P0

sample = random.sample(TASKS, n_tasks)
scores = []
for task in sample:
    review = get_review(P0, task["code"])
    fb     = score_review(review, task, condition)
    scores.append(fb["score"])

print(sum(scores) / len(scores))
