"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, base_url: str = "", model: str = "") -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    def chat_text(self, messages: list[dict[str, str]]) -> str:
        """Send messages and return plain text response."""
        raise NotImplementedError

    @abstractmethod
    def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Send messages and return parsed JSON response."""
        raise NotImplementedError

    @abstractmethod
    async def chat_text_async(self, messages: list[dict[str, str]]) -> str:
        """Asynchronously send messages and return plain text response."""
        raise NotImplementedError

    @abstractmethod
    async def chat_json_async(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Asynchronously send messages and return parsed JSON response."""
        raise NotImplementedError
