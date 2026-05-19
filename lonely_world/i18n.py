"""Internationalization support for lonely-world."""

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent
LOCALE_DIR = BASE_DIR / "locales"

_current_locale = "zh"


def set_locale(locale: str) -> None:
    global _current_locale
    _current_locale = locale


def get_locale() -> str:
    return _current_locale


def _load_locale(locale: str) -> dict[str, Any]:
    path = LOCALE_DIR / f"{locale}.json"
    if not path.exists():
        path = LOCALE_DIR / "zh.json"
    return json.loads(path.read_text(encoding="utf-8"))


_cached: dict[str, dict[str, Any]] = {}


def _get_locale_dict(locale: str) -> dict[str, Any]:
    if locale not in _cached:
        _cached[locale] = _load_locale(locale)
    return _cached[locale]


def _(key: str, locale: str = "", **kwargs: Any) -> str:
    """Translate a key like 'web.help_text' or 'cli.help_lines.0'.

    Dot notation indexes into nested dicts. kwargs are used for
    string formatting (e.g., '存档：{name}').
    """
    if not locale:
        locale = _current_locale
    d = _get_locale_dict(locale)
    for part in key.split("."):
        if isinstance(d, dict) and part in d:
            d = d[part]
        else:
            return key  # fallback: return the key itself
    if isinstance(d, list):
        return "\n".join(d)
    if isinstance(d, str):
        return d.format(**kwargs) if kwargs else d
    return key


def world_builder_prompts(round_index: int, qa: list, locale: str = "") -> tuple[str, str]:
    """Get world building system and user prompts for the given locale."""
    if not locale:
        locale = _current_locale
    system = _("world_builder.system_" + locale, locale=locale, round_index=round_index)
    user = _("world_builder.user_" + locale, locale=locale, qa=json.dumps(qa, ensure_ascii=False))
    return system, user