#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/opt/myapp")
CURRENT_LINK = APP_ROOT / "current"
PREVIOUS_LINK = APP_ROOT / "previous"
SYSTEMD_SERVICE = "myapp.service"

def run(cmd, cwd=None, check=True):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)

def rollback():
    if not PREVIOUS_LINK.is_symlink():
        raise SystemExit("No previous release to roll back to.")

    previous_target = PREVIOUS_LINK.resolve()
    print(f"Rolling back to: {previous_target}")

    if not previous_target.exists():
        raise SystemExit(f"Previous release path does not exist: {previous_target}")

    # Swap current -> previous target, and update previous to point to old current.
    if CURRENT_LINK.is_symlink():
        current_target = CURRENT_LINK.resolve()
        CURRENT_LINK.unlink()
        # Update previous to point to the old current.
        PREVIOUS_LINK.unlink()
        PREVIOUS_LINK.symlink_to(current_target)

    CURRENT_LINK.symlink_to(previous_target)
    print(f"Current release -> {previous_target}")

    # Graceful reload.
    run(["sudo", "systemctl", "reload", SYSTEMD_SERVICE])
    print("Rollback complete (zero-downtime reload triggered).")

def main():
    rollback()

if __name__ == "__main__":
    main()
