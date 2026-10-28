import json
from pathlib import Path

import config

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


def _load(language: str) -> dict[str, str]:
    with open(LOCALES_DIR / f"{language}.json", encoding="utf-8") as f:
        return json.load(f)


_fallback = _load("en")
_strings = _fallback if config.LANGUAGE == "en" else _load(config.LANGUAGE)


def t(key: str, **kwargs) -> str:
    """Return the translated string for `key`, falling back to English."""
    text = _strings.get(key) or _fallback.get(key) or key
    return text.format(**kwargs) if kwargs else text