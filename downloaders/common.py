import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PIL import Image
import yt_dlp


class MediaType(Enum):
    PHOTO = "photo"
    VIDEO = "video"


@dataclass
class MediaItem:
    type: MediaType
    path: str


URL_RE = re.compile(r"https?://\S+")

PLATFORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "instagram": re.compile(r"instagram\.com"),
    "tiktok": re.compile(r"tiktok\.com"),
    "threads": re.compile(r"threads\.net|threads\.com"),
    "twitter": re.compile(r"twitter\.com|x\.com"),
    "youtube": re.compile(r"youtube\.com/shorts|youtu\.be"),
    "reddit": re.compile(r"reddit\.com|redd\.it"),
    "erome": re.compile(r"erome\.com"),
}

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")


def extract_url(text: str) -> Optional[str]:
    match = URL_RE.search(text)
    return match.group(0) if match else None


def detect_platform(url: str) -> Optional[str]:
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return platform
    return None


def make_temp_dir() -> str:
    path = os.path.join(tempfile.gettempdir(), "tg_media_bot", uuid.uuid4().hex)
    os.makedirs(path, exist_ok=True)
    return path


def media_type_from_ext(path: str) -> Optional[MediaType]:
    ext = os.path.splitext(path)[1].lower()
    if ext in VIDEO_EXTS:
        return MediaType.VIDEO
    if ext in IMAGE_EXTS:
        return MediaType.PHOTO
    return None


def normalize_photo(path: str) -> str:
    root, _ext = os.path.splitext(path)
    jpg_path = root + ".jpg"
    tmp_path = root + ".normalized.jpg"

    try:
        with Image.open(path) as img:
            img.convert("RGB").save(tmp_path, "JPEG", quality=95)
    except Exception:
        return path

    if os.path.exists(path) and path != jpg_path:
        os.remove(path)
    os.replace(tmp_path, jpg_path)
    return jpg_path


def download_with_ytdlp(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s_%(autonumber)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
        "socket_timeout": 60,
        "retries": 3,
        "merge_output_format": "mp4",
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception:
        return None

    if info is None:
        return None

    entries = info.get("entries") or [info]

    items: list[MediaItem] = []
    for entry in entries:
        if not entry:
            continue
        filepath = ydl.prepare_filename(entry)
        if not os.path.exists(filepath):
            base, _ = os.path.splitext(filepath)
            for ext in (".mp4", ".jpg", ".jpeg", ".png", ".webp"):
                if os.path.exists(base + ext):
                    filepath = base + ext
                    break
        if not os.path.exists(filepath):
            continue
        media_type = media_type_from_ext(filepath)
        if media_type:
            items.append(MediaItem(type=media_type, path=filepath))

    return items if items else None
