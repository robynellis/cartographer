#!/usr/bin/env python3
import argparse
from pathlib import Path

from tqdm import tqdm
from yt_dlp import YoutubeDL

from config import load_config


def get_args():
    parser = argparse.ArgumentParser(description="Download audio from a YouTube playlist.")
    parser.add_argument(
        "--playlist",
        help="YouTube playlist URL. If omitted, uses download.playlist_url from vars.json",
    )
    return parser.parse_args()


def get_playlist_entries(playlist_url: str) -> list[str]:
    """
    Use yt-dlp to extract video URLs from a playlist without downloading.
    Normalizes entries so we always get a proper https://youtube.com/watch?v=... URL.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }

    urls: list[str] = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get("entries", []) or []

        for entry in entries:
            # Prefer full webpage URL if present
            url = entry.get("webpage_url") or entry.get("url")
            if not url:
                continue

            # If it's not a full URL, treat as video ID
            if not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={url}"

            urls.append(url)

    # Optional: remove duplicates while preserving order
    seen = set()
    normalized = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        normalized.append(u)

    return normalized


def write_songlist(base_dir: Path, urls: list[str]) -> Path:
    songlist_path = base_dir / "songlist"
    with songlist_path.open("w", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")
    return songlist_path


def download_audio(url: str, songs_dir: Path, audio_format: str):
    """
    Download audio from a single URL into songs_dir.
    Prefer the given format (e.g. 140), but fall back to best m4a / best.
    """
    format_selector = f"{audio_format}/bestaudio[ext=m4a]/bestaudio/best"

    ydl_opts = {
        "format": format_selector,
        "outtmpl": str(songs_dir / "%(title)s - %(uploader)s.%(ext)s"),
        "quiet": True,
        "noprogress": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main():
    cfg = load_config()
    args = get_args()

    base_dir = Path(cfg["base_dir"])
    songs_dir = base_dir / cfg["paths"]["songs"]
    songs_dir.mkdir(parents=True, exist_ok=True)

    audio_format = cfg["download"].get("audio_format", "140")
    cfg_playlist_url = cfg["download"].get("playlist_url") or ""
    playlist_url = args.playlist or cfg_playlist_url

    if not playlist_url:
        raise SystemExit("No playlist URL provided (CLI or vars.json).")

    print(f"[INFO] Using playlist: {playlist_url}")

    urls = get_playlist_entries(playlist_url)
    if not urls:
        raise SystemExit("[ERROR] No entries found in playlist.")

    print(f"[INFO] Found {len(urls)} videos in playlist.")
    songlist_path = write_songlist(base_dir, urls)
    print(f"[INFO] Wrote songlist to: {songlist_path}")

    use_progress = bool(cfg["download"].get("progress_bar", True))
    iterable = tqdm(urls, desc="Downloading audio", unit="video") if use_progress else urls

    for url in iterable:
        try:
            download_audio(url, songs_dir, audio_format)
        except Exception as e:
            msg = f"[ERROR] Failed to download {url}: {e}"
            if use_progress:
                tqdm.write(msg)
            else:
                print(msg)

    print("[DONE] Audio downloads complete.")


if __name__ == "__main__":
    main()