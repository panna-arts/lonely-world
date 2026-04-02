"""Anthropic Claude LLM provider."""

import json
import logging
from typing import Any, Optional, cast

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


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API."""

    def __init__(self, api_key: str, base_url: str = "", model: str = "") -> None:
        super().__init__(api_key, base_url, model)
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "Anthropic support requires the 'anthropic' package. "
                "Install it with: pip install anthropic"
            ) from exc

        if base_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            self.async_client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.async_client = anthropic.AsyncAnthropic(api_key=api_key)

    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[str, list[dict[str, Any]]]:
        """Extract system prompt and convert remaining messages to Claude format."""
        system_prompt = ""
        claude_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            elif msg.get("role") in ("user", "assistant"):
                claude_messages.append({"role": msg["role"], "content": msg["content"]})
        return system_prompt, claude_messages

    @with_retry(max_retries=2, base_delay=1.0)
    def chat_text(self, messages: list[dict[str, str]]) -> str:
        logger.debug("Anthropic chat_text request with %d messages", len(messages))
        system_prompt, claude_messages = self._convert_messages(messages)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        return content

    @with_retry(max_retries=2, base_delay=1.0)
    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        logger.debug("Anthropic chat_json request with %d messages", len(messages))
        system_prompt, claude_messages = self._convert_messages(messages)
        # Append JSON instruction to the last user message if present
        if claude_messages and claude_messages[-1]["role"] == "user":
            claude_messages[-1]["content"] += "\n\n请严格输出 JSON 格式，不要附加任何说明文字。"
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        parsed = _parse_json(content)
        return parsed or {}

    @with_retry_async(max_retries=2, base_delay=1.0)
    async def chat_text_async(self, messages: list[dict[str, str]]) -> str:
        logger.debug("Anthropic chat_text_async request with %d messages", len(messages))
        system_prompt, claude_messages = self._convert_messages(messages)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = await self.async_client.messages.create(**kwargs)
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        return content

    @with_retry_async(max_retries=2, base_delay=1.0)
    async def chat_json_async(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        logger.debug("Anthropic chat_json_async request with %d messages", len(messages))
        system_prompt, claude_messages = self._convert_messages(messages)
        if claude_messages and claude_messages[-1]["role"] == "user":
            claude_messages[-1]["content"] += "\n\n请严格输出 JSON 格式，不要附加任何说明文字。"
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = await self.async_client.messages.create(**kwargs)
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        parsed = _parse_json(content)
        return parsed or {}
