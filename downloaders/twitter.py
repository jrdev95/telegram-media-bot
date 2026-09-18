import math
import os
import re
from typing import Optional

import requests

from .common import MediaItem, MediaType, download_with_ytdlp

TWEET_ID_RE = re.compile(r"status/(\d+)")
HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE36_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    tweet_id = _extract_tweet_id(url)
    items = _download_via_syndication(tweet_id, out_dir) if tweet_id else None
    if items:
        return items
    return download_with_ytdlp(url, out_dir)


def _extract_tweet_id(url: str) -> Optional[str]:
    match = TWEET_ID_RE.search(url)
    return match.group(1) if match else None


def _generate_syndication_token(tweet_id: str) -> str:
    value = (int(tweet_id) / 1e15) * math.pi
    integer_part = int(value)
    fractional_part = value - integer_part

    int_str = ""
    n = integer_part
    while n > 0:
        int_str = BASE36_DIGITS[n % 36] + int_str
        n //= 36
    int_str = int_str or "0"

    frac_str = ""
    frac = fractional_part
    for _ in range(20):
        frac *= 36
        digit = int(frac)
        frac_str += BASE36_DIGITS[digit]
        frac -= digit
        if frac <= 1e-12:
            break

    token = (int_str + frac_str).replace("0", "").replace(".", "")
    return token[:10]


def _download_via_syndication(tweet_id: str, out_dir: str) -> Optional[list[MediaItem]]:
    token = _generate_syndication_token(tweet_id)
    api_url = (
        f"https://cdn.syndication.twimg.com/tweet-result"
        f"?id={tweet_id}&lang=en&token={token}"
    )
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=20)
        data = resp.json()
    except Exception:
        return None

    items: list[MediaItem] = []
    seen_urls: set[str] = set()

    video = data.get("video")
    if video:
        mp4_variants = [v for v in video.get("variants", []) if v.get("type") == "video/mp4"]
        if mp4_variants:
            best = max(mp4_variants, key=lambda v: v.get("bitrate", 0))
            video_url = best["src"]
            path = os.path.join(out_dir, "x_video.mp4")
            if _save(video_url, path):
                seen_urls.add(video_url)
                items.append(MediaItem(type=MediaType.VIDEO, path=path))

    for idx, photo in enumerate(data.get("photos", [])):
        photo_url = photo.get("url")
        if not photo_url or photo_url in seen_urls:
            continue
        seen_urls.add(photo_url)
        path = os.path.join(out_dir, f"x_photo_{idx}.jpg")
        if _save(photo_url, path):
            items.append(MediaItem(type=MediaType.PHOTO, path=path))

    return items if items else None


def _save(url: str, path: str) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        with open(path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
