"""Recover the probe pool: the 100 authored tasks excluded by benchmark.py's
seed-42 downsample. These have never been seen by training, validation, or the
benchmark channel — the held-out complement the spec's M1 builds pairs from.

Replicates benchmark.py:822-836 exactly: base(20) + EXTRA(180) in that order,
Random(42), sample(issue) then sample(clean) then shuffle. Any divergence from
that consumption order selects a different 100 — hence the hard asserts.
"""

import random

# Expected complement composition (verified 2026-07-28, recorded in the spec §6.3).
EXPECTED_TOTAL = 100
EXPECTED_BY_TYPE = {"security": 25, "correctness": 23, "maintainability": 26, "clean": 26}


def recover_complement() -> list[dict]:
    """Return the 100 excluded tasks as full task dicts.

    Excluded base-literal dicts exist nowhere at runtime (the downsample
    rebinds BENCHMARK_TASKS), so the authored base-20 list is recovered by
    re-executing benchmark.py's module prefix (task literals + detector defs,
    everything before the extended-tasks section) in an isolated namespace.
    """
    import benchmark
    from benchmark_tasks_extra import EXTRA_BENCHMARK_TASKS
    import pathlib

    src = pathlib.Path(benchmark.__file__).read_text()
    head = src[: src.index("# ── Extended benchmark tasks")]
    ns: dict = {}
    exec(compile(head, benchmark.__file__, "exec"), ns)  # module prefix only: literals + detector defs
    base = ns["BENCHMARK_TASKS"]
    assert len(base) == 20, f"base literal changed: {len(base)} tasks"

    full = base + list(EXTRA_BENCHMARK_TASKS)
    assert len(full) == 200, f"full pool changed: {len(full)} tasks"

    rng = random.Random(42)
    issue = [t for t in full if t["has_issue"]]
    clean = [t for t in full if not t["has_issue"]]
    n_issue = round(100 * len(issue) / len(full))
    n_clean = 100 - n_issue
    selected = rng.sample(issue, n_issue) + rng.sample(clean, n_clean)
    rng.shuffle(selected)

    selected_ids = {t["id"] for t in selected}
    live_ids = {t["id"] for t in benchmark.BENCHMARK_TASKS}
    assert selected_ids == live_ids, "replicated downsample diverges from benchmark.BENCHMARK_TASKS"

    complement = [t for t in full if t["id"] not in selected_ids]
    assert len(complement) == EXPECTED_TOTAL, f"complement size {len(complement)}"
    by_type: dict[str, int] = {}
    for t in complement:
        by_type[t["issue_type"]] = by_type.get(t["issue_type"], 0) + 1
    assert by_type == EXPECTED_BY_TYPE, f"complement composition changed: {by_type}"
    return complement


def pool_by_category() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for t in recover_complement():
        out.setdefault(t["issue_type"], []).append(t)
    return out
