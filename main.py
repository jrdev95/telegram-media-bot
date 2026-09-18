import logging
import shutil
import time
from typing import BinaryIO

import telebot
from telebot import apihelper, types

from config import BOT_TOKEN
from downloaders import erome, instagram, reddit, threads, tiktok, twitter, youtube
from downloaders.common import MediaItem, MediaType, detect_platform, extract_url, make_temp_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("media_bot")

apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

DOWNLOADERS = {
    "instagram": instagram.download,
    "tiktok": tiktok.download,
    "threads": threads.download,
    "twitter": twitter.download,
    "youtube": youtube.download,
    "reddit": reddit.download,
    "erome": erome.download,
}

MAX_ALBUM_SIZE = 10
DOWNLOADING_TEXT = "⏳ Fazendo o download..."
FAILED_TEXT = "❌ Não foi possível baixar nenhuma mídia neste link!"

BOT_START_TIME = time.time()


@bot.message_handler(commands=["start", "help"])
def handle_start(message: types.Message) -> None:
    bot.reply_to(
        message,
        "Envie (ou encaminhe) uma mensagem com um link do Instagram, TikTok, "
        "Threads, X, YouTube Shorts, Reddit ou Erome que eu respondo com a "
        "mídia baixada.",
    )


@bot.message_handler(func=lambda m: extract_url(m.text or "") is not None, content_types=["text"])
def handle_link(message: types.Message) -> None:
    if message.date < BOT_START_TIME:
        return

    url = extract_url(message.text)
    if url is None:
        return

    platform = detect_platform(url)
    if not platform:
        return

    downloader = DOWNLOADERS[platform]
    out_dir = make_temp_dir()
    status_message = bot.reply_to(message, DOWNLOADING_TEXT)

    try:
        bot.send_chat_action(message.chat.id, "upload_video")
        items = downloader(url, out_dir)

        if not items:
            _mark_as_failed(status_message)
            return

        _send_media(message, items)
        bot.delete_message(status_message.chat.id, status_message.message_id)

    except Exception:
        logger.exception("Erro ao processar link: %s", url)
        _mark_as_failed(status_message)
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def _mark_as_failed(status_message: types.Message) -> None:
    try:
        bot.edit_message_text(
            FAILED_TEXT,
            chat_id=status_message.chat.id,
            message_id=status_message.message_id,
        )
    except Exception:
        pass


def _send_media(message: types.Message, items: list[MediaItem]) -> None:
    items = items[:MAX_ALBUM_SIZE]

    if len(items) == 1:
        item = items[0]
        with open(item.path, "rb") as f:
            if item.type == MediaType.VIDEO:
                bot.send_video(message.chat.id, f, reply_to_message_id=message.message_id)
            else:
                bot.send_photo(message.chat.id, f, reply_to_message_id=message.message_id)
        return

    open_files: list[BinaryIO] = []
    try:
        media_group: list[types.InputMedia] = []
        for item in items:
            f = open(item.path, "rb")
            open_files.append(f)
            if item.type == MediaType.VIDEO:
                media_group.append(types.InputMediaVideo(f))
            else:
                media_group.append(types.InputMediaPhoto(f))

        bot.send_media_group(message.chat.id, media_group, reply_to_message_id=message.message_id)
    finally:
        for f in open_files:
            f.close()


if __name__ == "__main__":
    logger.info("Bot iniciado. Aguardando mensagens...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
