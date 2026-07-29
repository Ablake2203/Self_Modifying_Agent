"""CHARTER CLI — see DETAILS_/charter_framework.md.

Usage:
  python run_charter.py smoke                    # delegate to smoke_test_charter.py
  python run_charter.py campaign --stage retest|controls|v2
  python run_charter.py m3-sheet                 # (re)generate annotation sheet
  python run_charter.py report
  python run_charter.py m5 <run.json>            # AVR over a run's adoptions
  python run_charter.py screen <run.json>        # M6 triage
"""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="CHARTER measurement CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("smoke")
    camp = sub.add_parser("campaign")
    camp.add_argument("--stage", choices=["retest", "controls", "v2"], required=True)
    sub.add_parser("m3-sheet")
    sub.add_parser("freeze-pairs")
    sub.add_parser("report")
    m5p = sub.add_parser("m5")
    m5p.add_argument("run_json")
    scr = sub.add_parser("screen")
    scr.add_argument("run_json")
    args = ap.parse_args()

    if args.cmd == "smoke":
        import smoke_test_charter
        sys.exit(smoke_test_charter.main())
    elif args.cmd == "campaign":
        from charter.campaign import STAGES
        STAGES[args.stage]()
    elif args.cmd == "freeze-pairs":
        from charter.gen_pairs import DRAFT, FROZEN
        from charter.pairs import load_pairs
        if FROZEN.exists():
            raise SystemExit("pairs_v1.json already frozen")
        if not DRAFT.exists():
            raise SystemExit("no draft — run python -m charter.gen_pairs first")
        load_pairs(DRAFT)  # revalidate before freezing
        DRAFT.rename(FROZEN)
        print(f"frozen: {FROZEN}")
    elif args.cmd == "m3-sheet":
        from charter.m3_ledger import generate_sheet
        generate_sheet()
        print("sheet written (blank) — use charter/gen_m3_prefill.py output if re-prefilling")
    elif args.cmd == "report":
        from charter.report import build_report
        try:
            from charter.m3_ledger import load_annotations
            e_scores = load_annotations()["e_scores"]
        except (FileNotFoundError, ValueError) as e:
            print(f"[report] E-channel unavailable ({e}); reporting without K-A-E cube")
            e_scores = None
        print(build_report(e_scores))
    elif args.cmd == "m5":
        from charter.m5_avr import adoption_records
        recs = adoption_records(Path(args.run_json))
        print(json.dumps([{k: v for k, v in r.items() if k != "text"} for r in recs],
                         indent=1)[:4000])
        print(f"{len(recs)} adoptions (full AVR needs degraded_events from verdicts)")
    elif args.cmd == "screen":
        from charter.m6_screen import screen_run
        print(json.dumps(screen_run(Path(args.run_json)), indent=1))


if __name__ == "__main__":
    main()
