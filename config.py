# config.py
import json
from pathlib import Path

def load_config(path: str | None = None):
    """
    Load vars.json and normalize base_dir to an absolute path.
    If base_dir is '.', treat it as the project root.
    """
    if path:
        cfg_path = Path(path)
    else:
        cfg_path = Path(__file__).parent / "vars.json"

    with cfg_path.open(encoding="utf-8") as f:
        cfg = json.load(f)

    # Resolve base_dir
    base_dir = Path(cfg.get("base_dir", "."))
    if str(base_dir) == ".":
        # Project root (directory where config.py lives)
        cfg["base_dir"] = Path(__file__).parent.resolve()
    else:
        cfg["base_dir"] = base_dir.resolve()

    return cfg