import os
from typing import Optional

import requests

from .common import MediaItem, MediaType, download_with_ytdlp

HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    items = download_with_ytdlp(url, out_dir)
    if items and len(items) > 1:
        return items

    fallback_items = _download_via_tikwm(url, out_dir)
    if fallback_items:
        return fallback_items

    return items


def _resolve_video_url(url: str) -> str:
    try:
        resp = requests.head(url, allow_redirects=True, headers=HEADERS, timeout=15)
        return resp.url
    except Exception:
        return url


def _download_via_tikwm(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    final_url = _resolve_video_url(url)
    api_url = "https://www.tikwm.com/api/"
    try:
        resp = requests.get(
            api_url, params={"url": final_url, "hd": 1}, headers=HEADERS, timeout=20
        )
        payload = resp.json()
        data = payload.get("data")
        if not data:
            return None
    except Exception:
        return None

    items: list[MediaItem] = []

    images = data.get("images")
    if images:
        for idx, img_url in enumerate(images):
            path = os.path.join(out_dir, f"tiktok_photo_{idx}.jpg")
            if _save(img_url, path):
                items.append(MediaItem(type=MediaType.PHOTO, path=path))
        return items if items else None

    video_url = data.get("hdplay") or data.get("play")
    if video_url:
        path = os.path.join(out_dir, "tiktok_video.mp4")
        if _save(video_url, path):
            items.append(MediaItem(type=MediaType.VIDEO, path=path))

    return items if items else None


def _save(url: str, path: str) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        with open(path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
