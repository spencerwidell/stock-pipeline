"""Backfill newly-added universe names IMMEDIATELY — no gaps, no waiting for the
nightly close or the quarterly fundamentals/moat run.

The Manage-tab "Add a company" form fires this in the background so a new name is
FULLY scored within a few minutes: price history, VSA features + signals,
conviction, fundamentals (F-score), and moat. It reuses the exact nightly code
paths (run_daily.sh + the quarterly scripts), so an onboarded name is identical to
one the cron would have produced — no second, divergent single-ticker pipeline.

Concurrency: whole-universe scripts overwrite shared parquets, so two runs at once
would race. A flock-based lock guarantees one run at a time; if a run is already in
flight when another add fires, we set a rerun flag and exit. The running job loops
while that flag is set, and since fetch_stock.py re-reads universe.yaml each pass,
names added mid-run are naturally picked up. So rapid successive adds coalesce into
at most one extra pass instead of N overlapping rebuilds.

Steps per pass:
  1. scripts/run_daily.sh   price -> VSA -> signals -> conviction (fund=0 for new)
  2. fetch_fundamentals.py  F-score (full rebuild; picks up new names)
  3. conviction_score.py    re-run so the new F-scores credit into conviction
  4. moat_score.py          staleness-guarded -> scores only the new/stale names

Telegram is NOT triggered (run_daily only pushes when SEND_TELEGRAM=1, which we
never set here), so onboarding a name won't ping the phone.

Usage:
  python onboard.py              # run the backfill (used by the dashboard, detached)
  python onboard.py --status     # print "running" or "idle" and exit
"""

import fcntl
import os
import subprocess
import sys
from datetime import datetime

LOCK_PATH = "/tmp/stockpipe_onboard.lock"
FLAG_PATH = "/tmp/stockpipe_onboard.rerun"
LOG_PATH  = "logs/onboard.log"

# Each step: (label, argv). run_daily.sh self-activates conda; the python scripts
# are run with the same interpreter that launched us (the dashboard's stock env).
STEPS = [
    ("pipeline",     ["bash", "scripts/run_daily.sh"]),
    ("fundamentals", [sys.executable, "fetch_fundamentals.py"]),
    ("conviction",   [sys.executable, "conviction_score.py"]),
    ("moat",         [sys.executable, "moat_score.py"]),
]


def _log(msg):
    os.makedirs("logs", exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{stamp}] {msg}\n")


def is_running():
    """True if a backfill currently holds the lock."""
    if not os.path.exists(LOCK_PATH):
        return False
    f = open(LOCK_PATH, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    else:
        fcntl.flock(f, fcntl.LOCK_UN)
        return False
    finally:
        f.close()


def _run_pass():
    with open(LOG_PATH, "a") as logf:
        for label, argv in STEPS:
            _log(f"  -> {label}: {' '.join(argv)}")
            rc = subprocess.run(argv, stdout=logf, stderr=subprocess.STDOUT).returncode
            _log(f"  <- {label} finished (rc={rc})")


def main():
    if "--status" in sys.argv:
        print("running" if is_running() else "idle")
        return

    lock = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # A backfill is already in flight — ask it to run once more (so our newly
        # added ticker, already written to universe.yaml, gets picked up) and exit.
        open(FLAG_PATH, "w").close()
        _log("backfill already running; requested a rerun and exited")
        return

    try:
        _log("=== onboarding backfill started ===")
        while True:
            if os.path.exists(FLAG_PATH):
                os.remove(FLAG_PATH)          # claim the pending rerun before this pass
            _run_pass()
            if not os.path.exists(FLAG_PATH):  # nothing queued during the pass -> done
                break
            _log("rerun flag set during pass; looping to pick up newer adds")
        _log("=== onboarding backfill complete ===")
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    main()
