"""Shared utilities for LLM providers."""

import json
from typing import Any, Optional, cast


def parse_json(text: str) -> Optional[dict[str, Any]]:
    """Parse JSON from text, with fallback extraction of JSON object from markdown.

    Returns None if no valid JSON is found.
    """
    try:
        return cast(dict[str, Any], json.loads(text))
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return cast(dict[str, Any], json.loads(text[start : end + 1]))
            except json.JSONDecodeError:
                return None
    return None