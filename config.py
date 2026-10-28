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
SUPPORT_CATEGORY_ID = int(_required("SUPPORT_CATEGORY_ID"))
PARTNERSHIP_CATEGORY_ID = int(_required("PARTNERSHIP_CATEGORY_ID"))

# Maps each ticket kind to its Discord category
TICKET_CATEGORIES = {
    "support": SUPPORT_CATEGORY_ID,
    "partnership": PARTNERSHIP_CATEGORY_ID,
}
TRANSCRIPT_CHANNEL_ID = int(_required("TRANSCRIPT_CHANNEL_ID"))

LANGUAGE = os.getenv("LANGUAGE", "en").lower()
TIMEZONE = os.getenv("TIMEZONE", "Europe/Rome")

if LANGUAGE not in SUPPORTED_LANGUAGES:
    raise RuntimeError(
        f"Unsupported LANGUAGE '{LANGUAGE}'. Choose one of: {', '.join(SUPPORTED_LANGUAGES)}"
    )