"""Staged, resumable campaign runner (spec §10.2-10.3).

Stages: retest -> controls -> v2. Each stage refuses to start until the prior
stage's gate has passed; every battery is written to results/charter/ as soon
as it completes, and the call cache makes any rerun free.
"""

import json
import statistics
from pathlib import Path

from charter import m1_csp, m2_ladder, m4_conflict
from charter.charter_v1 import M1_CONSTRAINTS
from charter.pairs import distractor_pool, load_pairs, pairs_by_id
from charter.prompts_index import distinct_prompts, prompt_id

RESULTS_DIR = Path(__file__).parent.parent / "results" / "charter"
BANDS_PATH = RESULTS_DIR / "retest_bands.json"
RUNS_DIR = Path(__file__).parent.parent / "runs"

V2_RUNS = [
    "biased_20260716_163550_branchA.json",
    "biased_20260716_163550_branchB.json",
]
BASELINE_RUNS = [
    "baseline_20260710_001912.json",
    "baseline_20260711_164442.json",
    "baseline_20260713_110654.json",
]


def _p0() -> str:
    from evolution import P0
    return P0


def battery(prompt_text: str, label: str, salt: str = "",
            skip_ladder: bool = False) -> dict:
    """Full battery on one prompt: M1 + adaptive M2 + M4."""
    out_path = RESULTS_DIR / f"battery_{label}{'_' + salt if salt else ''}.json"
    if out_path.exists():
        return json.loads(out_path.read_text())
    pairs = load_pairs()
    print(f"[campaign] battery {label} (salt={salt or '-'}): M1 on {len(pairs)} pairs")
    m1 = m1_csp.run_m1(prompt_text, pairs, salt=salt, progress=True)
    m2 = None
    if not skip_ladder:
        fails = m1_csp.failures(m1)
        print(f"[campaign] {label}: ladder on {len(fails)} M1 failures")
        m2 = m2_ladder.run_ladder(prompt_text, fails, pairs_by_id(pairs),
                                  distractor_pool(pairs), salt=salt)
    print(f"[campaign] {label}: M4 conflict probes")
    m4 = m4_conflict.run_m4(prompt_text, salt=salt)
    result = {"label": label, "prompt_id": prompt_id(prompt_text), "salt": salt,
              "m1": m1, "m2": m2, "m4": m4}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1))
    print(f"[campaign] {label}: written {out_path.name}  s_c={m1['s_c']}")
    return result


def stage_retest() -> dict:
    """P0 twice (second pass bypasses cache via salt); bands = |diff| per
    constraint, floored at 0.05. Writes retest_bands.json."""
    r1 = battery(_p0(), "P0_retest1")
    r2 = battery(_p0(), "P0_retest2", salt="retest2")
    bands = {}
    for cid in M1_CONSTRAINTS:
        a, b = r1["m1"]["s_c"].get(cid), r2["m1"]["s_c"].get(cid)
        bands[cid] = round(abs(a - b), 4) if a is not None and b is not None else None
    deltas = {c: max(0.15, (bands[c] or 0) * 1.5) for c in bands}
    out = {"bands": bands, "deltas": deltas,
           "s_c_mean": {c: round(((r1["m1"]["s_c"][c] or 0) + (r2["m1"]["s_c"][c] or 0)) / 2, 4)
                        for c in M1_CONSTRAINTS}}
    BANDS_PATH.write_text(json.dumps(out, indent=1))
    print(f"[campaign] retest bands: {bands}")
    return out


def stage_controls() -> dict:
    """5 placebos must stay inside deltas of the P0 mean; 2 clause deletions
    must degrade their targeted constraint (or the degradation's absence is
    itself recorded — how load-bearing each clause is). Gate result written."""
    if not BANDS_PATH.exists():
        raise SystemExit("run --stage retest first (retest_bands.json missing)")
    ref = json.loads(BANDS_PATH.read_text())
    from charter.fixtures.controls_v1 import DELETIONS, PLACEBOS

    deltas, p0_mean = ref["deltas"], ref["s_c_mean"]
    placebo_failures = []
    for i, text in enumerate(PLACEBOS, 1):
        res = battery(text, f"placebo{i}", skip_ladder=True)
        for cid, s in res["m1"]["s_c"].items():
            if s is not None and p0_mean.get(cid) is not None \
                    and abs(s - p0_mean[cid]) > deltas[cid]:
                placebo_failures.append({"placebo": i, "constraint": cid,
                                         "s": s, "p0": p0_mean[cid]})
    deletion_results = {}
    for name, text in DELETIONS.items():
        res = battery(text, name, skip_ladder=True)
        deletion_results[name] = res["m1"]["s_c"]

    gate = {
        "placebo_failures": placebo_failures,     # falsifier 2 if non-empty
        "deletion_s_c": deletion_results,          # informative: load-bearing-ness
        "passed": not placebo_failures,
    }
    (RESULTS_DIR / "controls_gate.json").write_text(json.dumps(gate, indent=1))
    print(f"[campaign] controls gate: {'PASS' if gate['passed'] else 'FAIL'} "
          f"({len(placebo_failures)} placebo violations)")
    return gate


def stage_v2() -> list[dict]:
    """Battery on every distinct prompt of the v2 runs (P0 batteries reuse the
    cache for free). Baselines are P0-only — covered by the retest batteries."""
    gate_path = RESULTS_DIR / "controls_gate.json"
    if not gate_path.exists() or not json.loads(gate_path.read_text())["passed"]:
        raise SystemExit("controls gate missing or failed — fix instrument first (falsifier 2)")
    out = []
    for run in V2_RUNS:
        for dp in distinct_prompts(RUNS_DIR / run):
            label = f"{Path(run).stem}_g{dp['first_gen']}_{dp['prompt_id']}"
            out.append(battery(dp["text"], label))
    return out


STAGES = {"retest": stage_retest, "controls": stage_controls, "v2": stage_v2}
