import os
import re
from typing import Optional

import instaloader

from .common import MediaItem, MediaType, download_with_ytdlp, media_type_from_ext

SHORTCODE_RE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:p|reel|tv)/([^/?#&]+)")


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    items = download_with_ytdlp(url, out_dir)
    if items:
        return items
    return _download_with_instaloader(url, out_dir)


def _extract_shortcode(url: str) -> Optional[str]:
    match = SHORTCODE_RE.search(url)
    return match.group(1) if match else None


def _download_with_instaloader(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    shortcode = _extract_shortcode(url)
    if not shortcode:
        return None

    try:
        loader = instaloader.Instaloader(
            dirname_pattern=out_dir,
            filename_pattern="{shortcode}_{mediaid}",
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            post_metadata_txt_pattern="",
            quiet=True,
        )
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target="")
    except Exception:
        return None

    items: list[MediaItem] = []
    for fname in sorted(os.listdir(out_dir)):
        full_path = os.path.join(out_dir, fname)
        media_type = media_type_from_ext(full_path)
        if media_type:
            items.append(MediaItem(type=media_type, path=full_path))

    return items if items else None
