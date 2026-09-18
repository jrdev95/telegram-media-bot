from typing import Optional

from .common import MediaItem, download_with_ytdlp


def download(url: str, out_dir: str) -> Optional[list[MediaItem]]:
    return download_with_ytdlp(url, out_dir)
