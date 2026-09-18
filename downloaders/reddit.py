import html
import os
import re
import subprocess
from typing import Optional
from urllib.parse import urlencode, urljoin

from curl_cffi import requests

from .common import MediaItem, MediaType, download_with_ytdlp

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
AUDIO_CANDIDATES = ("DASH_audio.mp4", "DASH_AUDIO_128.mp4", "DASH_AUDIO_64.mp4")

CHALLENGE_TOKEN_RE = re.compile(r'\(async e=>e\+e\)\("([0-9a-f]+)"\)')
CHALLENGE_ACTION_RE = re.compile(r'<form[^>]+action="([^"]+)"')
CHALLENGE_JSC_TOKEN_RE = re.compile(r'name="jsc_token" value="([^"]+)"')


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    session = requests.Session()
    resolved_url = _resolve_url(session, url)
    post = _fetch_post_data(session, resolved_url)

    if not post:
        return download_with_ytdlp(resolved_url, out_dir)

    if post.get("is_gallery") and post.get("media_metadata"):
        return _download_gallery(post, out_dir)

    if post.get("is_video"):
        return _download_video_post(post, out_dir)

    direct_url = post.get("url_overridden_by_dest") or post.get("url")
    if direct_url and _looks_like_image(direct_url):
        return _download_single_image(direct_url, out_dir)

    return download_with_ytdlp(resolved_url, out_dir)


def _resolve_url(session, url: str) -> str:
    try:
        resp = session.get(url, headers=HEADERS, allow_redirects=True, timeout=15, impersonate="chrome")
        resp = _pass_challenge_if_needed(session, resp)
        return resp.url
    except Exception:
        return url


def _pass_challenge_if_needed(session, resp):
    if not _is_challenge_page(resp.text):
        return resp

    solved_url = _solve_challenge(resp.text, resp.url)
    if not solved_url:
        return resp

    try:
        new_resp = session.get(solved_url, headers=HEADERS, allow_redirects=True, timeout=15, impersonate="chrome")
        return new_resp
    except Exception:
        return resp


def _is_challenge_page(page_html: str) -> bool:
    return 'name="solution"' in page_html and "js_challenge" in page_html


def _solve_challenge(page_html: str, base_url: str) -> Optional[str]:
    token_match = CHALLENGE_TOKEN_RE.search(page_html)
    action_match = CHALLENGE_ACTION_RE.search(page_html)
    jsc_token_match = CHALLENGE_JSC_TOKEN_RE.search(page_html)
    if not (token_match and action_match and jsc_token_match):
        return None

    token = token_match.group(1)
    solution = token + token
    action = action_match.group(1)
    jsc_token = jsc_token_match.group(1)

    target = urljoin(base_url, action)
    query = urlencode({"solution": solution, "js_challenge": "1", "jsc_token": jsc_token, "jsc_orig_r": ""})
    return f"{target}?{query}"


def _fetch_post_data(session, url: str) -> Optional[dict]:
    json_url = url.split("?")[0].rstrip("/") + ".json"
    try:
        resp = session.get(json_url, headers=HEADERS, timeout=20, impersonate="chrome")
        resp = _pass_challenge_if_needed(session, resp)
        data = resp.json()
        return data[0]["data"]["children"][0]["data"]
    except Exception:
        return None


def _looks_like_image(url: str) -> bool:
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    return ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _download_single_image(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
    path = os.path.join(out_dir, f"reddit_photo{ext}")
    if _save(url, path):
        return [MediaItem(type=MediaType.PHOTO, path=path)]
    return None


def _download_gallery(post: dict, out_dir: str) -> Optional[list[MediaItem]]:
    items: list[MediaItem] = []
    gallery_items = post.get("gallery_data", {}).get("items", [])
    media_metadata = post.get("media_metadata", {})

    for idx, gallery_item in enumerate(gallery_items):
        media_id = gallery_item.get("media_id")
        meta = media_metadata.get(media_id)
        if not meta or meta.get("status") != "valid":
            continue

        media_kind = meta.get("e")
        source = meta.get("s", {})

        if media_kind == "AnimatedImage" and source.get("mp4"):
            media_url = html.unescape(source["mp4"])
            path = os.path.join(out_dir, f"reddit_{idx}.mp4")
            if _save(media_url, path):
                items.append(MediaItem(type=MediaType.VIDEO, path=path))
        elif source.get("u"):
            media_url = html.unescape(source["u"])
            path = os.path.join(out_dir, f"reddit_{idx}.jpg")
            if _save(media_url, path):
                items.append(MediaItem(type=MediaType.PHOTO, path=path))

    return items if items else None


def _download_video_post(post: dict, out_dir: str) -> Optional[list[MediaItem]]:
    reddit_video = post.get("media", {}).get("reddit_video") or post.get(
        "secure_media", {}
    ).get("reddit_video")
    if not reddit_video:
        return None

    video_url = reddit_video.get("fallback_url")
    if not video_url:
        return None
    video_url = video_url.split("?")[0]

    video_path = os.path.join(out_dir, "reddit_video_only.mp4")
    if not _save(video_url, video_path):
        return None

    audio_path = _download_matching_audio(video_url, out_dir)
    final_path = os.path.join(out_dir, "reddit_video.mp4")

    if audio_path and _merge_audio_video(video_path, audio_path, final_path):
        return [MediaItem(type=MediaType.VIDEO, path=final_path)]

    return [MediaItem(type=MediaType.VIDEO, path=video_path)]


def _download_matching_audio(video_url: str, out_dir: str) -> Optional[str]:
    base_url = video_url.rsplit("/", 1)[0]
    for candidate in AUDIO_CANDIDATES:
        audio_url = f"{base_url}/{candidate}"
        path = os.path.join(out_dir, "reddit_audio_only.mp4")
        if _save(audio_url, path, min_size=1024):
            return path
    return None


def _merge_audio_video(video_path: str, audio_path: str, output_path: str) -> bool:
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c",
                "copy",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                output_path,
            ],
            capture_output=True,
            timeout=60,
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception:
        return False


def _save(url: str, path: str, min_size: int = 0) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, impersonate="chrome")
        if resp.status_code != 200 or len(resp.content) <= min_size:
            return False
        with open(path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception:
        return False
