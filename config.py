import os

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_LANGUAGES = ("en", "it")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing '{name}': check your .env file")
    return value


TOKEN = _required("DISCORD_TOKEN")
GUILD_ID = int(_required("GUILD_ID"))
STAFF_ROLE_ID = int(_required("STAFF_ROLE_ID"))
TRANSCRIPT_CHANNEL_ID = int(_required("TRANSCRIPT_CHANNEL_ID"))

SUPPORT_CATEGORY_ID = int(_required("SUPPORT_CATEGORY_ID"))
PARTNERSHIP_CATEGORY_ID = int(_required("PARTNERSHIP_CATEGORY_ID"))

# Maps each ticket kind to its Discord category
TICKET_CATEGORIES = {
    "support": SUPPORT_CATEGORY_ID,
    "partnership": PARTNERSHIP_CATEGORY_ID,
}

# BOT_LANGUAGE (not LANGUAGE) to avoid clashing with the system locale variable
LANGUAGE = (os.getenv("BOT_LANGUAGE") or "en").strip().lower()
TIMEZONE = (os.getenv("TIMEZONE") or "Europe/Rome").strip()

# Seconds a user must wait after a ticket is closed before opening a new one
TICKET_COOLDOWN = int(os.getenv("TICKET_COOLDOWN") or 300)

if LANGUAGE not in SUPPORTED_LANGUAGES:
    raise RuntimeError(
        f"Unsupported BOT_LANGUAGE '{LANGUAGE}'. Choose one of: {', '.join(SUPPORTED_LANGUAGES)}"
    )