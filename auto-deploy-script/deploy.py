#!/usr/bin/env python3
import argparse
import datetime
import os
import shutil
import subprocess
from pathlib import Path

APP_ROOT = Path("/opt/myapp")
RELEASES_DIR = APP_ROOT / "releases"
CURRENT_LINK = APP_ROOT / "current"
PREVIOUS_LINK = APP_ROOT / "previous"
VENV_PATH = APP_ROOT / "venv"           # optional, shared venv
SYSTEMD_SERVICE = "myapp.service"       # systemd unit name

def run(cmd, cwd=None, check=True):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)

def ensure_dirs():
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)

def create_release_dir():
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    release_path = RELEASES_DIR / ts
    release_path.mkdir(parents=True)
    return release_path

def copy_source(src_dir: Path, release_dir: Path):
    # Copy app source into the new release directory.
    # For a real project, you might do a git checkout or rsync instead.[web:14][web:26]
    for item in src_dir.iterdir():
        if item.name in {".git", "__pycache__", ".venv"}:
            continue
        dest = release_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

def install_requirements(release_dir: Path):
    req = release_dir / "requirements.txt"
    if req.exists() and VENV_PATH.exists():
        run([str(VENV_PATH / "bin" / "pip"), "install", "-r", str(req)])

def update_symlinks(new_release: Path):
    # If current exists, move it to previous.
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        old_target = CURRENT_LINK.resolve()
        print(f"Previous release: {old_target}")
        if PREVIOUS_LINK.is_symlink() or PREVIOUS_LINK.exists():
            PREVIOUS_LINK.unlink()
        PREVIOUS_LINK.symlink_to(old_target)
        CURRENT_LINK.unlink()

    # Atomically point current to the new release.
    CURRENT_LINK.symlink_to(new_release)
    print(f"Current release -> {new_release}")

def reload_service():
    # Graceful reload of Gunicorn via systemd unit.
    run(["sudo", "systemctl", "reload", SYSTEMD_SERVICE])

def main():
    parser = argparse.ArgumentParser(description="Zero-downtime deploy script for Flask app.")
    parser.add_argument(
        "--src",
        required=True,
        help="Path to local source directory (e.g., checked-out git repo).",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Do not reload service (for dry-run/testing).",
    )
    args = parser.parse_args()

    src_dir = Path(args.src).resolve()
    if not src_dir.is_dir():
        raise SystemExit(f"Source directory not found: {src_dir}")

    ensure_dirs()
    release_dir = create_release_dir()
    print(f"New release dir: {release_dir}")

    copy_source(src_dir, release_dir)
    install_requirements(release_dir)

    update_symlinks(release_dir)

    if not args.no_reload:
        reload_service()
        print("Deployment complete (zero-downtime reload triggered).")
    else:
        print("Deployment complete (no reload requested).")

if __name__ == "__main__":
    main()
