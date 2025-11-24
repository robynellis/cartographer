#!/usr/bin/env python3
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError, Page
from tqdm import tqdm

from config import load_config


FILE_INPUT_SELECTOR = "input[type='file']"
SLIDER_SELECTOR = "div.level-right svg#red"
ARTIST_INPUT_SELECTOR = "input[placeholder='Song Artist']"
ADVANCED_TOGGLE_SELECTOR = "svg:has(path[d='M3 6L9 12L15 6'])"
# MODEL_SELECT_SELECTOR is built dynamically from config


def slide_to_generate(page: Page, slider_selector: str):
    slider = page.locator(slider_selector).first
    slider.wait_for(state="visible", timeout=10_000)

    box = slider.bounding_box()
    if box is None:
        raise RuntimeError("Could not get bounding box for slider")

    start_x = box["x"] + box["width"] * 0.2
    start_y = box["y"] + box["height"] * 0.5
    end_x = box["x"] + box["width"] * 0.8
    end_y = start_y

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y, steps=30)
    page.mouse.up()


def iter_audio_files(songs_dir: Path):
    exts = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".aac", ".aiff"}
    for f in sorted(songs_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in exts:
            yield f


def main():
    cfg = load_config()

    base_dir = Path(cfg["base_dir"])
    songs_dir = base_dir / cfg["paths"]["songs"]
    maps_dir = base_dir / cfg["paths"]["maps"]
    maps_dir.mkdir(parents=True, exist_ok=True)

    beatsage_cfg = cfg["beatsage"]
    beatsage_url = beatsage_cfg["url"]
    headless = bool(beatsage_cfg.get("headless", True))
    artist_name = beatsage_cfg["artist_name"]
    difficulty_label = beatsage_cfg["difficulty_label"]
    model_value = beatsage_cfg["model_value"]
    timeout_minutes = beatsage_cfg.get("download_timeout_minutes", 10)
    download_timeout_ms = timeout_minutes * 60 * 1000

    model_select_selector = f"select:has(option[value='{model_value}'])"

    audio_files = list(iter_audio_files(songs_dir))
    if not audio_files:
        print(f"[INFO] No audio files found in {songs_dir}")
        return

    print(f"[INFO] Found {len(audio_files)} audio files in {songs_dir}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        for audio in tqdm(audio_files, desc="Generating maps", unit="map"):
            base = audio.stem
            existing_zips = list(maps_dir.glob(f"*{base}*.zip"))
            if existing_zips:
                tqdm.write(f"[SKIP] Map already exists for {base}")
                continue

            tqdm.write(f"[MAP] Generating map for {audio.name}")

            # 1. Open BeatSage
            page.goto(beatsage_url, wait_until="networkidle")

            # 2. Upload audio file
            page.set_input_files(FILE_INPUT_SELECTOR, str(audio))

            # 3. Fill in artist name
            try:
                artist_input = page.locator(ARTIST_INPUT_SELECTOR).first
                artist_input.wait_for(state="visible", timeout=10_000)
                artist_input.fill(artist_name)
            except Exception as e:
                tqdm.write(f"[WARN] Could not fill artist for {audio.name}: {e}")

            # 4. Enable desired difficulty
            try:
                expert_label = page.locator(
                    "span.control-label",
                    has_text=difficulty_label
                ).first
                expert_label.wait_for(state="visible", timeout=10_000)
                expert_label.click()
            except Exception as e:
                tqdm.write(f"[WARN] Could not set difficulty {difficulty_label} for {audio.name}: {e}")

            # 5. Expand advanced options and select model version
            try:
                advanced_toggle = page.locator(ADVANCED_TOGGLE_SELECTOR).first
                advanced_toggle.wait_for(state="visible", timeout=10_000)
                advanced_toggle.click()

                model_select = page.locator(model_select_selector).first
                model_select.wait_for(state="visible", timeout=10_000)
                model_select.select_option(model_value)
            except Exception as e:
                tqdm.write(f"[WARN] Could not set model {model_value} for {audio.name}: {e}")

            # 6. Slide to trigger generation and wait for download
            try:
                with page.expect_download(timeout=download_timeout_ms) as dl_info:
                    slide_to_generate(page, SLIDER_SELECTOR)

                download = dl_info.value
                suggested = download.suggested_filename
                target = maps_dir / suggested
                download.save_as(str(target))

                tqdm.write(f"[OK] Saved map to {target}")

            except TimeoutError:
                tqdm.write(f"[TIMEOUT] No download for {audio.name} within timeout")
            except Exception as e:
                tqdm.write(f"[ERROR] Failed for {audio.name}: {e}")

        browser.close()


if __name__ == "__main__":
    main()