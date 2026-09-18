import os
import re
from typing import Iterable, Optional

import requests

from .common import MediaItem, MediaType

USER_AGENTS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
]

CANONICAL_RE = re.compile(r'<link rel="canonical" href="[^"]*?/post/([^/"?]+)')

VIDEO_JSON_RE = re.compile(r'"video_versions":\[\{[^}]*?"url":"([^"]+)"')
IMAGE_JSON_RE = re.compile(r'"image_versions2":\{"candidates":\[\{[^}]*?"url":"([^"]+)"')

OG_VIDEO_RE = re.compile(
    r'<meta[^>]+property="og:video(?::secure_url)?"[^>]+content="([^"]+)"'
)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"')


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    html = _fetch_html(url)
    if not html:
        return None

    video_urls, image_urls = _extract_target_post_media(html)

    if not video_urls and not image_urls:
        video_urls = _unique(_decode(u) for u in OG_VIDEO_RE.findall(html))
        image_urls = _unique(_decode(u) for u in OG_IMAGE_RE.findall(html))

    items: list[MediaItem] = []

    for idx, vid_url in enumerate(video_urls):
        path = os.path.join(out_dir, f"threads_video_{idx}.mp4")
        if _save(vid_url, path):
            items.append(MediaItem(type=MediaType.VIDEO, path=path))

    if not video_urls:
        for idx, img_url in enumerate(image_urls):
            path = os.path.join(out_dir, f"threads_photo_{idx}.jpg")
            if _save(img_url, path):
                items.append(MediaItem(type=MediaType.PHOTO, path=path))

    return items if items else None


def _extract_target_post_media(html: str) -> tuple[list[str], list[str]]:
    canonical_match = CANONICAL_RE.search(html)
    if not canonical_match:
        return [], []
    shortcode = canonical_match.group(1)

    code_marker = f'"code":"{shortcode}"'
    code_idx = html.find(code_marker)
    if code_idx == -1:
        return [], []

    cm_key_idx = html.rfind('"carousel_media":', 0, code_idx)

    if cm_key_idx != -1:
        value_start = cm_key_idx + len('"carousel_media":')
        if html[value_start] == "[":
            end_idx = _find_matching_bracket(html, value_start)
            if end_idx != -1:
                segment = html[value_start : end_idx + 1]
                video_urls = _unique(_decode(u) for u in VIDEO_JSON_RE.findall(segment))
                image_urls = _unique(_decode(u) for u in IMAGE_JSON_RE.findall(segment))
                return video_urls, image_urls

    segment_end = html.find('"code":"', code_idx + len(code_marker))
    if segment_end == -1:
        segment_end = len(html)
    segment = html[code_idx:segment_end]

    video_urls = _unique(_decode(u) for u in VIDEO_JSON_RE.findall(segment))[:1]
    image_urls = _unique(_decode(u) for u in IMAGE_JSON_RE.findall(segment))[:1]
    return video_urls, image_urls


def _find_matching_bracket(html: str, start_idx: int) -> int:
    depth = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(html)):
        ch = html[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return i
    return -1


def _fetch_html(url: str) -> Optional[str]:
    for user_agent in USER_AGENTS:
        try:
            resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=20)
            html = resp.text
        except Exception:
            continue

        if "video_versions" in html or "image_versions2" in html or "og:image" in html:
            return html

    return None


def _decode(raw_url: str) -> str:
    unescaped = raw_url.replace("\\/", "/")
    return unescaped.encode().decode("unicode_escape")


def _unique(iterable: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _save(url: str, path: str) -> bool:
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Referer": "https://www.threads.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200 or not resp.content:
            return False
        with open(path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
