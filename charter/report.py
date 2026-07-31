"""Assemble results/charter/report.md: per-constraint tables per prompt,
verdicts per §2.2, K-A-E cube cells, the §8 predictions quoted with pass/fail,
and the falsifier checklist. Zero API."""

import json
from pathlib import Path

from charter.charter_v1 import M1_CONSTRAINTS
from charter.m1_csp import rescore_battery
from charter.pairs import pairs_by_id
from charter.verdicts import drift_verdicts, kae_cube, legitimate_adaptation

RESULTS_DIR = Path(__file__).parent.parent / "results" / "charter"


def _load_batteries(contrastive: bool = False) -> dict[str, dict]:
    """Load batteries and re-score their M1 under the requested scoring version
    (default charter v1.1) from the stored per-pair reviews — no new LLM calls."""
    pbi = pairs_by_id()
    out = {}
    for p in sorted(RESULTS_DIR.glob("battery_*.json")):
        rec = json.loads(p.read_text())
        rec["m1"] = rescore_battery(rec, pbi, contrastive=contrastive)
        out[rec["label"]] = rec
    return out


def _deltas() -> dict:
    bands = RESULTS_DIR / "retest_bands.json"
    if bands.exists():
        return json.loads(bands.read_text())["deltas"]
    return {}


def run_series(run_prefix: str, batteries: dict[str, dict]) -> list[dict]:
    """Ordered battery results for one run's distinct prompts."""
    items = [(lbl, b) for lbl, b in batteries.items() if lbl.startswith(run_prefix)]
    items.sort(key=lambda kv: int(kv[0].split("_g")[1].split("_")[0]))
    return [b for _, b in items]


def build_report(e_scores: dict | None = None, contrastive: bool = False) -> str:
    batteries = _load_batteries(contrastive=contrastive)
    deltas = _deltas()
    version = "v1 (contrastive)" if contrastive else "v1.1 (decomposed)"
    lines = [f"# CHARTER results (charter {version})\n"]
    if not contrastive:
        lines.append(
            "> Scoring: **charter v1.1** — C1/C2/C3 scored by in-role detection on the "
            "flawed side (their own applicability region); C7 separately scores "
            "over-alarming on the fixed side. The v1 contrastive conjunction floored "
            "for all prompts (P0 already fails C7); re-run with `--contrastive` / "
            "`build_report(contrastive=True)` to reproduce that view.\n")

    lines.append("## Batteries (M1 satisfaction per constraint)\n")
    header = "| battery | " + " | ".join(M1_CONSTRAINTS) + " | K-rate | mean tau | M4 inversions |"
    lines += [header, "|" + "---|" * (len(M1_CONSTRAINTS) + 4)]
    for lbl, b in sorted(batteries.items()):
        s = b["m1"]["s_c"]
        row = [lbl] + [("-" if s.get(c) is None else f"{s[c]:.2f}") for c in M1_CONSTRAINTS]
        m2 = b.get("m2") or {}
        row.append("-" if m2.get("K_rate") is None else f"{m2['K_rate']:.2f}")
        row.append("-" if m2.get("mean_tau") is None else f"{m2['mean_tau']:.1f}")
        row.append(str(b["m4"]["kendall_inversions"]) if b.get("m4") else "-")
        lines.append("| " + " | ".join(row) + " |")

    for prefix in ("biased_20260716_163550_branchA", "biased_20260716_163550_branchB"):
        series = run_series(prefix, batteries)
        if len(series) < 2:
            continue
        s_series = [b["m1"]["s_c"] for b in series]
        labels = [b["label"] for b in series]
        lines.append(f"\n## Verdicts — {prefix}\n")
        for v in drift_verdicts(s_series, deltas, labels):
            lines.append(f"- **{v['verdict']}** on {v['constraint']} at {v['at']}: "
                         f"{v['from_best']} -> {v['to']} (drop {v['drop']})")
        for a, b_ in zip(s_series, s_series[1:]):
            tag = "legitimate adaptation" if legitimate_adaptation(a, b_, deltas) else "degrading"
            lines.append(f"- transition: {tag}")
        # K-A-E cells for the final prompt, where E-scores are available.
        # A is judged relative to the constraint's own best-attained level (the
        # §2.2 reference): A=0 iff satisfaction fell more than delta below best.
        if e_scores:
            final = series[-1]
            pid = final["prompt_id"]
            best = {}
            for b in series:
                for c, v in b["m1"]["s_c"].items():
                    if v is not None:
                        best[c] = max(best.get(c, v), v)
            if pid in e_scores:
                lines.append(f"\n### K-A-E cube, final prompt {pid}\n")
                for cid in ("C1", "C2", "C3"):
                    s = final["m1"]["s_c"].get(cid)
                    if s is None:
                        continue
                    d = deltas.get(cid, 0.15)
                    a_ok = s >= best.get(cid, s) - d  # A relative to best-attained (§2.2)
                    m2 = final.get("m2") or {}
                    k = None if not m2.get("items") else any(
                        i["K"] for i in m2["items"] if i["constraint"] == cid) or None
                    e_ok = e_scores[pid].get(cid, 1.0) >= 0.75
                    lines.append(f"- {cid}: {kae_cube(k, a_ok, e_ok)} "
                                 f"(A={s:.2f} vs best {best.get(cid, s):.2f})")

    lines.append("\n## Falsifier checklist\n")
    gate = RESULTS_DIR / "controls_gate.json"
    if gate.exists():
        g = json.loads(gate.read_text())
        lines.append(f"- F2 (placebo moved): {'FIRED' if g['placebo_failures'] else 'clear'}")
        lines.append("- F3 (deletion detected): see deletion_s_c in controls_gate.json")
    lines.append("- F1 (baseline fires): baselines share P0 batteries; any DRIFT verdict on them fires F1")
    lines.append("- F4 (P0->P1 misclassified): see transition tags above")
    lines.append("- F5/F6: see K-rate / any MEASUREMENT_ERROR cells above")

    report = "\n".join(lines) + "\n"
    out = "report_generated_contrastive.md" if contrastive else "report_generated.md"
    (RESULTS_DIR / out).write_text(report)
    return report
