#!/usr/bin/env python3
import json
import zipfile
import re
from pathlib import Path

from config import load_config


def clean_name(name: str) -> str:
    """
    Clean Beat Sage naming:
    - Remove 'Beat Sage_' prefix
    - Remove trailing ' (....)' metadata blocks
    - Remove embedded audio extensions like '.m4a', '.mp3', '.wav', etc.
    - Remove bracketed tags like '[Official Audio]'
    - Simplify patterns like 'Artist - (Title) [tag] - Artist' -> 'Title - Artist'
    """
    # Remove prefix
    if name.startswith("Beat Sage_"):
        name = name.replace("Beat Sage_", "", 1).strip()

    # Remove trailing parentheses metadata, e.g. " (v2-flow HEE+,S9,DO)"
    name = re.sub(r"\s*\([^()]*\)$", "", name).strip()

    # Remove audio extensions wherever they appear as a token
    name = re.sub(r"\.(m4a|mp3|wav|ogg|flac|aac)\b", "", name, flags=re.IGNORECASE)

    # Remove bracketed tags like [Official Audio]
    name = re.sub(r"\s*\[[^\]]*\]", "", name).strip()

    # Remove wrapping parentheses around title fragments, e.g. "(The Forgotten People)" -> "The Forgotten People"
    name = re.sub(r"\(([^()]+)\)", r"\1", name)

    # Special case: "Artist - Title - Artist" -> "Title - Artist"
    parts = [p.strip() for p in name.split(" - ") if p.strip()]
    if len(parts) == 3 and parts[0].lower() == parts[2].lower():
        name = f"{parts[1]} - {parts[0]}"
    else:
        name = " - ".join(parts)

    # Cleanup double spaces
    name = re.sub(r"\s{2,}", " ", name).strip()

    return name


def unzip_all_maps(maps_dir: Path):
    """
    Unzip all ZIPs in maps_dir into folders under maps_dir using cleaned names.
    """
    if not maps_dir.exists():
        print(f"[ERROR] Maps directory does not exist: {maps_dir}")
        return

    zips = list(maps_dir.glob("*.zip"))
    if not zips:
        print(f"[INFO] No ZIP files found in {maps_dir}")
        return

    for zip_path in zips:
        clean_stem = clean_name(zip_path.stem)
        extract_path = maps_dir / clean_stem

        if extract_path.exists():
            print(f"[SKIP] Folder already exists for {zip_path.name}: {extract_path.name}")
            continue

        print(f"[UNZIP] {zip_path.name} → {extract_path.name}/")
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)
        except Exception as e:
            print(f"[ERROR] Failed to extract {zip_path.name}: {e}")
            # best-effort cleanup of partial folder
            for child in extract_path.iterdir():
                if child.is_file():
                    child.unlink()
            extract_path.rmdir()


def find_info_dat(folder: Path) -> Path | None:
    direct = folder / "Info.dat"
    if direct.exists():
        return direct

    for p in folder.iterdir():
        if p.is_file() and p.name.lower() == "info.dat":
            return p

    return None


def update_info_dat(maps_dir: Path, author_name: str):
    """
    Modify Info.dat in each extracted map folder:
    - Set _levelAuthorName
    - Remove _creator
    - Remove root-level _customData
    """
    for folder in maps_dir.iterdir():
        if not folder.is_dir():
            continue

        info_dat = find_info_dat(folder)
        if info_dat is None:
            print(f"[WARN] No Info.dat found in {folder.name}")
            continue

        try:
            data = json.loads(info_dat.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ERROR] Failed to read/parse Info.dat in {folder.name}: {e}")
            continue

        data["_levelAuthorName"] = author_name

        if "_creator" in data:
            del data["_creator"]

        if "_customData" in data:
            del data["_customData"]

        try:
            info_dat.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"[EDIT] Cleaned Info.dat in {folder.name}")
        except Exception as e:
            print(f"[ERROR] Failed writing Info.dat in {folder.name}: {e}")


def clean_difficulty_files(maps_dir: Path):
    """
    Remove _customData from all difficulty *.dat files.
    """
    keys_to_scan = [
        "_notes",
        "_sliders",
        "_obstacles",
        "_events",
        "_chains",
        "_waypoints",
    ]

    for folder in maps_dir.iterdir():
        if not folder.is_dir():
            continue

        for dat_file in folder.glob("*.dat"):
            if dat_file.name.lower() == "info.dat":
                continue

            try:
                data = json.loads(dat_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[ERROR] Failed to read/parse {dat_file.name} in {folder.name}: {e}")
                continue

            modified = False

            if "_customData" in data:
                del data["_customData"]
                modified = True

            for key in keys_to_scan:
                arr = data.get(key)
                if not isinstance(arr, list):
                    continue
                for obj in arr:
                    if isinstance(obj, dict) and "_customData" in obj:
                        del obj["_customData"]
                        modified = True

            if not modified:
                continue

            try:
                dat_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                print(f"[CLEAN] Removed custom data from {dat_file.name} in {folder.name}")
            except Exception as e:
                print(f"[ERROR] Failed writing {dat_file.name} in {folder.name}: {e}")


def main():
    cfg = load_config()
    base_dir = Path(cfg["base_dir"])
    maps_dir = base_dir / cfg["paths"]["maps"]
    author_name = cfg["postprocess"]["author_name"]

    print("=== Unzipping Beat Sage maps ===")
    unzip_all_maps(maps_dir)

    print("=== Updating Info.dat author and cleaning custom data ===")
    update_info_dat(maps_dir, author_name)

    print("=== Cleaning difficulty .dat files (removing _customData) ===")
    clean_difficulty_files(maps_dir)

    print("=== Done. Maps are cleaned and ready for ChroMapper. ===")


if __name__ == "__main__":
    main()