"""Supported report languages and server-authored presentation messages."""

import json
from pathlib import Path
from typing import Literal

ResponseLanguage = Literal["en", "ar"]
LANGUAGES = {"en": "English", "ar": "Modern Standard Arabic"}
_CATALOG_DIR = Path(__file__).parent / "catalogs"
CATALOGS = {
    code: json.loads((_CATALOG_DIR / f"{code}.json").read_text(encoding="utf-8")) for code in LANGUAGES
}


def text(language: ResponseLanguage, key: str, **values) -> str:
    return CATALOGS.get(language, CATALOGS["en"])[key].format(**values)
