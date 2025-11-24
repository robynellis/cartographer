#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from config import load_config


VENV_DIR = Path(".venv")
REQUIREMENTS = Path("requirements.txt")


def create_venv_if_needed():
    """
    Create the virtual environment if missing, and install dependencies.
    """
    if not VENV_DIR.exists():
        print("\n=== Creating virtual environment (.venv) ===")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    else:
        print("\n=== Virtual environment already exists ===")

    pip = VENV_DIR / "bin" / "pip"
    if not pip.exists():
        raise RuntimeError("pip not found in the virtual environment.")

    if REQUIREMENTS.exists():
        print("=== Installing dependencies ===")
        subprocess.run([str(pip), "install", "-r", str(REQUIREMENTS)], check=True)
    else:
        print("=== No requirements.txt found, skipping dependency installation ===")


def run_step(name: str, command: list[str], yes: bool = False):
    """
    Runs a subprocess step with clear output separation.
    """
    print(f"\n=== {name} ===")

    if not yes:
        ans = input(f"Run step '{name}'? [Y/n] ").strip().lower()
        if ans == "n":
            print(f"[SKIP] {name}")
            return

    try:
        subprocess.run(command, check=True)
        print(f"[OK] {name} completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Step '{name}' failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run full Cartographer pipeline.")
    parser.add_argument("--config", help="Path to vars.json")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--skip-clean", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Run all steps without prompting (CI mode)")
    args = parser.parse_args()

    # Load config
    cfg = load_config(args.config) if args.config else load_config()

    project_root = Path(__file__).parent

    print("==========================================")
    print("         🚀 Cartographer Pipeline         ")
    print("==========================================")
    print(f"Using base directory: {cfg['base_dir']}")
    print("")

    # 0. Ensure venv exists + install deps
    create_venv_if_needed()

    # Use the venv's Python interpreter
    python = str(VENV_DIR / "bin" / "python")

    # 1. Download songs
    if not args.skip_download:
        run_step(
            "Download Songs",
            [python, str(project_root / "download_songs.py")],
            yes=args.yes
        )

    # 2. Generate maps
    if not args.skip_generate:
        run_step(
            "Generate Maps",
            [python, str(project_root / "generate_maps.py")],
            yes=args.yes
        )

    # 3. Clean maps
    if not args.skip_clean:
        run_step(
            "Clean/Finalize Maps",
            [python, str(project_root / "manipulate_files.py")],
            yes=args.yes
        )

    print("\n==========================================")
    print("      🎉 Pipeline Complete Successfully    ")
    print("==========================================\n")


if __name__ == "__main__":
    main()