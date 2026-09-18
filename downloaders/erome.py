import os
import re
from typing import Iterable, Optional

import requests

from .common import MediaItem, MediaType

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.erome.com/",
}

IMAGE_RE = re.compile(r'<img[^>]+class="[^"]*\bimg-(?:front|back)\b[^"]*"[^>]+(?:data-src|src)="([^"]+)"')
VIDEO_RE = re.compile(r'<source[^>]+src="([^"]+)"')


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        page_html = resp.text
    except Exception:
        return None

    video_urls = _unique(VIDEO_RE.findall(page_html))
    image_urls = _unique(IMAGE_RE.findall(page_html))

    items: list[MediaItem] = []

    for idx, vid_url in enumerate(video_urls):
        path = os.path.join(out_dir, f"erome_video_{idx}.mp4")
        if _save(vid_url, path):
            items.append(MediaItem(type=MediaType.VIDEO, path=path))

    for idx, img_url in enumerate(image_urls):
        path = os.path.join(out_dir, f"erome_photo_{idx}.jpg")
        if _save(img_url, path):
            items.append(MediaItem(type=MediaType.PHOTO, path=path))

    return items if items else None


def _unique(iterable: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _save(url: str, path: str) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200 or not resp.content:
            return False
        with open(path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
