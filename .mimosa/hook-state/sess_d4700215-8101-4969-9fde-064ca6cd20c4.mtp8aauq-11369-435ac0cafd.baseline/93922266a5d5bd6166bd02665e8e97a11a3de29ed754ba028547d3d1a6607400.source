"""Tests for LLM providers."""

from unittest.mock import MagicMock, patch

import pytest

from lonely_world.llm.anthropic_provider import AnthropicProvider
from lonely_world.llm.base import LLMProvider
from lonely_world.llm.factory import create_provider
from lonely_world.llm.openai_provider import OpenAIProvider


class DummyProvider(LLMProvider):
    def chat_text(self, messages):
        return "hello"

    def chat_json(self, messages):
        return {"reply": "hello"}

    async def chat_text_async(self, messages):
        return "hello async"

    async def chat_json_async(self, messages):
        return {"reply": "hello async"}


class TestFactory:
    def test_create_openai(self):
        p = create_provider("openai", "key", "https://api.openai.com/v1", "gpt-4")
        assert isinstance(p, OpenAIProvider)

    def test_create_ollama(self):
        p = create_provider("ollama", "key", "http://localhost:11434/v1", "llama3")
        assert isinstance(p, OpenAIProvider)

    @pytest.mark.skipif(
        "__import__('importlib.util', fromlist=['util']).find_spec('anthropic') is None",
        reason="anthropic not installed",
    )
    def test_create_claude(self):
        p = create_provider("anthropic", "key", model="claude-3")
        assert isinstance(p, AnthropicProvider)

    def test_unsupported_provider(self):
        with pytest.raises(ValueError):
            create_provider("unknown", "key")


class TestOpenAIProvider:
    @patch("lonely_world.llm.openai_provider.OpenAI")
    def test_chat_text(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="reply text"))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider("key", "https://api.example.com/v1", "gpt-4")
        result = provider.chat_text([{"role": "user", "content": "hi"}])
        assert result == "reply text"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4", messages=[{"role": "user", "content": "hi"}]
        )

    @patch("lonely_world.llm.openai_provider.OpenAI")
    def test_chat_json(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"reply": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider("key", model="gpt-4")
        result = provider.chat_json([{"role": "user", "content": "hi"}])
        assert result == {"reply": "ok"}
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            response_format={"type": "json_object"},
        )

    @pytest.mark.anyio
    @patch("lonely_world.llm.openai_provider.AsyncOpenAI")
    async def test_chat_text_async(self, mock_async_cls):
        import asyncio

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="async text"))]
        future = asyncio.Future()
        future.set_result(mock_completion)
        mock_client.chat.completions.create.return_value = future
        mock_async_cls.return_value = mock_client

        provider = OpenAIProvider("key", model="gpt-4")
        result = await provider.chat_text_async([{"role": "user", "content": "hi"}])
        assert result == "async text"

    @pytest.mark.anyio
    @patch("lonely_world.llm.openai_provider.AsyncOpenAI")
    async def test_chat_json_async(self, mock_async_cls):
        import asyncio

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"reply": "async"}'))]
        future = asyncio.Future()
        future.set_result(mock_completion)
        mock_client.chat.completions.create.return_value = future
        mock_async_cls.return_value = mock_client

        provider = OpenAIProvider("key", model="gpt-4")
        result = await provider.chat_json_async([{"role": "user", "content": "hi"}])
        assert result == {"reply": "async"}


@pytest.mark.skipif(
    "__import__('importlib.util', fromlist=['util']).find_spec('anthropic') is None",
    reason="anthropic not installed",
)
class TestAnthropicProvider:
    @patch("anthropic.Anthropic")
    def test_chat_text(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "claude reply"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        provider = AnthropicProvider("key", model="claude-3")
        result = provider.chat_text([{"role": "user", "content": "hi"}])
        assert result == "claude reply"

    @patch("anthropic.Anthropic")
    def test_chat_json(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.text = '{"reply": "ok"}'
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        provider = AnthropicProvider("key", model="claude-3")
        result = provider.chat_json([{"role": "user", "content": "hi"}])
        assert result == {"reply": "ok"}

    @pytest.mark.anyio
    @patch("anthropic.AsyncAnthropic")
    async def test_chat_text_async(self, mock_async_cls):
        import asyncio

        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "async claude"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        future = asyncio.Future()
        future.set_result(mock_response)
        mock_client.messages.create.return_value = future
        mock_async_cls.return_value = mock_client

        provider = AnthropicProvider("key", model="claude-3")
        result = await provider.chat_text_async([{"role": "user", "content": "hi"}])
        assert result == "async claude"

    @pytest.mark.anyio
    @patch("anthropic.AsyncAnthropic")
    async def test_chat_json_async(self, mock_async_cls):
        import asyncio

        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.text = '{"reply": "async"}'
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        future = asyncio.Future()
        future.set_result(mock_response)
        mock_client.messages.create.return_value = future
        mock_async_cls.return_value = mock_client

        provider = AnthropicProvider("key", model="claude-3")
        result = await provider.chat_json_async([{"role": "user", "content": "hi"}])
        assert result == {"reply": "async"}
