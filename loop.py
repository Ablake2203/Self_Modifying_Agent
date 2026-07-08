"""
Continuous autonomous loop.

Runs run_experiment() indefinitely, checkpointing after every generation.
Resumes from last checkpoint on restart or crash.
Writes a regression alert and pauses if accuracy drops >10% from peak.

Usage:
    python loop.py --condition truthful
    python loop.py --condition biased --reset   # ignore existing checkpoint
"""

import argparse
import time
from pathlib import Path

from state import save, load, write_alert, clear

REGRESSION_THRESHOLD = 0.10   # pause if accuracy drops more than this from peak
ALERT_POLL_INTERVAL  = 30     # seconds to wait between alert-dir checks


def _alert_pending() -> bool:
    return bool(list(Path("alerts").glob("alert_*.md"))) if Path("alerts").exists() else False


def run_continuous(condition: str) -> None:
    checkpoint_path = Path("state.json")
    peak_accuracy   = 0.0

    print(f"\n{'='*60}")
    print(f"  Continuous loop — condition: {condition.upper()}")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Regression threshold: >{REGRESSION_THRESHOLD:.0%} drop from peak")
    print(f"{'='*60}\n")

    while True:
        # ── Load checkpoint ────────────────────────────────────────────────
        checkpoint = load(checkpoint_path)
        if checkpoint:
            peak_accuracy = checkpoint.get("peak_accuracy", 0.0)
            gen           = checkpoint.get("generation", 0)
            print(f"  [loop] Resuming from gen {gen}  (peak accuracy {peak_accuracy:.2%})")
        else:
            print(f"  [loop] No checkpoint — starting fresh.")

        # ── Run one epoch ─────────────────────────────────────────────────
        from evolution import run_experiment

        def on_checkpoint(state: dict) -> None:
            nonlocal peak_accuracy

            acc = state.get("last_accuracy")
            state["peak_accuracy"] = peak_accuracy

            if acc is not None:
                if acc > peak_accuracy:
                    peak_accuracy = acc
                    state["peak_accuracy"] = peak_accuracy
                    print(f"  [loop] New peak accuracy: {peak_accuracy:.2%}")

                # Regression check
                if peak_accuracy > 0 and acc < peak_accuracy * (1 - REGRESSION_THRESHOLD):
                    msg = (
                        f"Regression detected at generation {state['generation']}.\n"
                        f"Current accuracy: {acc:.2%}\n"
                        f"Peak accuracy:    {peak_accuracy:.2%}\n"
                        f"Drop:             {(peak_accuracy - acc):.2%}\n\n"
                        f"Delete this file to resume the loop."
                    )
                    alert_path = write_alert(msg)
                    print(f"\n  [loop] REGRESSION ALERT written to {alert_path}")
                    print(f"  [loop] Pausing until alert is cleared...")
                    while _alert_pending():
                        time.sleep(ALERT_POLL_INTERVAL)
                    print(f"  [loop] Alert cleared — resuming.")

            save(state, checkpoint_path)

        run_experiment(condition, checkpoint=checkpoint, on_checkpoint=on_checkpoint)
        print(f"  [loop] Epoch complete. Restarting in 3s...\n")
        time.sleep(3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuous self-evolving loop")
    parser.add_argument(
        "--condition", choices=["biased", "truthful", "baseline"],
        required=True, help="Feedback condition",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear existing checkpoint and start fresh",
    )
    args = parser.parse_args()

    if args.reset:
        clear()
        print("  [loop] Checkpoint cleared.")

    try:
        run_continuous(args.condition)
    except KeyboardInterrupt:
        print("\n  [loop] Stopped by user. Checkpoint preserved — run again to resume.")


if __name__ == "__main__":
    main()
