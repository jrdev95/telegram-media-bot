import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN não encontrado. Crie um arquivo .env (copie o .env.example) "
        "e coloque o token do bot obtido com o @BotFather em BOT_TOKEN=..."
    )
