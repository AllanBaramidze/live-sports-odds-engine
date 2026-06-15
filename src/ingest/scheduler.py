"""
runs espn_schedule.py & valkeydb.py every hour to maintain correctness of matchups
"""

import schedule
import time
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime

# logging settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS = {
    "espn_schedule": BASE_DIR / "src" / "ingest" / "espn_ingest" / "espn_schedule.py",
    "valkey_sync": BASE_DIR / "src" / "db" / "valkeydb.py",
}

# config
ESPN_INTERVAL_HOURS = 1


def verify_paths():
    """Verify all script paths exist on startup."""
    all_ok = True
    for name, path in SCRIPTS.items():
        if path.exists():
            logger.info(f"  [OK] {name}: {path}")
        else:
            logger.error(f"  [MISSING] {name}: {path}")
            all_ok = False
    return all_ok


def run_script(name: str) -> bool:
    """Run a script by name. Returns True on success."""
    path = SCRIPTS[name]
    logger.info(f"Running {name}...")

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.info(f"  [{name}] {line}")
        logger.info(f"{name} completed successfully.")
        return True
    else:
        logger.error(f"{name} failed (exit code {result.returncode}).")
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                logger.error(f"  [{name}] {line}")
        return False


def scheduled_sync():
    """ESPN -> Postgres -> Valkey pipeline."""
    logger.info("=" * 50)
    logger.info("Starting scheduled sync...")
    logger.info("=" * 50)

    if not run_script("espn_schedule"):
        logger.warning("Skipping Valkey sync due to ESPN failure.")
        return

    run_script("valkey_sync")
    logger.info("Scheduled sync complete.\n")


def main():
    logger.info(f"Scheduler starting (Python: {sys.executable})")
    logger.info(f"Project root: {BASE_DIR}")

    if not verify_paths():
        logger.error("Missing scripts. Fix paths and restart.")
        sys.exit(1)

    # Run once immediately on startup
    scheduled_sync()

    # Then schedule recurring runs
    schedule.every(ESPN_INTERVAL_HOURS).hours.do(scheduled_sync)
    logger.info(f"Scheduled: ESPN sync every {ESPN_INTERVAL_HOURS} hour(s)")
    logger.info("Press CTRL+C to quit.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()