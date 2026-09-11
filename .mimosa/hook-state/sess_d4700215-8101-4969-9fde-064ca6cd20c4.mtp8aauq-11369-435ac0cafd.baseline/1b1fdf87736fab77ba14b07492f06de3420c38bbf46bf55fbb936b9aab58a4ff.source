"""Server-Sent Events helpers."""

import json
from typing import Any


def format_sse(data: dict[str, Any]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
