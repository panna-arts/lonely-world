"""OpenAI-compatible LLM provider."""

import json
import logging
from typing import Any, Optional, cast

from openai import AsyncOpenAI, OpenAI

from lonely_world.llm.base import LLMProvider
from lonely_world.llm.retry import with_retry, with_retry_async

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> Optional[dict[str, Any]]:
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


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI and OpenAI-compatible APIs."""

    def __init__(self, api_key: str, base_url: str = "", model: str = "") -> None:
        super().__init__(api_key, base_url, model)
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)

    @with_retry(max_retries=2, base_delay=1.0)
    def chat_text(self, messages: list[dict[str, str]]) -> str:
        logger.debug("OpenAI chat_text request with %d messages", len(messages))
        completion = self.client.chat.completions.create(
            model=self.model, messages=cast(Any, messages)
        )
        return completion.choices[0].message.content or ""

    @with_retry(max_retries=2, base_delay=1.0)
    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        logger.debug("OpenAI chat_json request with %d messages", len(messages))
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=cast(Any, messages),
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or "{}"
        parsed = _parse_json(content)
        return parsed or {}

    @with_retry_async(max_retries=2, base_delay=1.0)
    async def chat_text_async(self, messages: list[dict[str, str]]) -> str:
        logger.debug("OpenAI chat_text_async request with %d messages", len(messages))
        completion = await self.async_client.chat.completions.create(
            model=self.model, messages=cast(Any, messages)
        )
        return completion.choices[0].message.content or ""

    @with_retry_async(max_retries=2, base_delay=1.0)
    async def chat_json_async(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        logger.debug("OpenAI chat_json_async request with %d messages", len(messages))
        completion = await self.async_client.chat.completions.create(
            model=self.model,
            messages=cast(Any, messages),
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or "{}"
        parsed = _parse_json(content)
        return parsed or {}
