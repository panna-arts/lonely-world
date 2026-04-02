"""Session management for the Web UI."""

import os
import uuid
from typing import Optional

from fastapi import Request

from lonely_world.config import load_config
from lonely_world.game.engine import GameEngine
from lonely_world.game.world import WorldBuilder
from lonely_world.llm.base import LLMProvider
from lonely_world.llm.factory import create_provider
from lonely_world.models import GameConfig


class WebConfigError(RuntimeError):
    """Raised when server configuration is incomplete for web mode."""

    pass


class SessionStore:
    """In-memory store for active sessions."""

    def __init__(self) -> None:
        self._engines: dict[str, GameEngine] = {}
        self._builders: dict[str, WorldBuilder] = {}
        self._names: dict[str, str] = {}
        self._story_append: dict[str, bool] = {}
        self._provider: Optional[LLMProvider] = None
        self._config: Optional[GameConfig] = None

    def load_server_config(self) -> GameConfig:
        """Load and validate global server config (non-interactive)."""
        cfg = load_config()
        # Prefer env vars for web mode
        cfg.api_key = (
            os.getenv("OPENAI_API_KEY") or os.getenv("LONELY_WORLD_API_KEY") or cfg.api_key
        )
        cfg.base_url = (
            os.getenv("OPENAI_BASE_URL") or os.getenv("LONELY_WORLD_BASE_URL") or cfg.base_url
        )
        cfg.model = os.getenv("LONELY_WORLD_MODEL") or cfg.model or ""

        if not cfg.api_key:
            raise WebConfigError(
                "API Key 未配置。请设置环境变量 OPENAI_API_KEY 或 LONELY_WORLD_API_KEY。"
            )
        if not cfg.base_url:
            raise WebConfigError(
                "Base URL 未配置。请设置环境变量 OPENAI_BASE_URL 或 LONELY_WORLD_BASE_URL。"
            )
        if not cfg.model:
            raise WebConfigError("模型名称未配置。请设置环境变量 LONELY_WORLD_MODEL。")
        self._config = cfg
        self._provider = create_provider(
            provider=cfg.provider,
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            model=cfg.model,
        )
        return cfg

    @property
    def config(self) -> GameConfig:
        if self._config is None:
            raise WebConfigError("Server config not loaded yet.")
        return self._config

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            raise WebConfigError("Server config not loaded yet.")
        return self._provider

    def ensure_session_id(self, request: Request) -> str:
        sid = request.session.get("id")
        if not sid:
            sid = str(uuid.uuid4())
            request.session["id"] = sid
        return sid

    def get_engine(self, session_id: str) -> Optional[GameEngine]:
        return self._engines.get(session_id)

    def set_engine(self, session_id: str, engine: GameEngine) -> None:
        self._engines[session_id] = engine

    def get_builder(self, session_id: str) -> Optional[WorldBuilder]:
        return self._builders.get(session_id)

    def set_builder(self, session_id: str, builder: WorldBuilder) -> None:
        self._builders[session_id] = builder

    def clear_builder(self, session_id: str) -> None:
        self._builders.pop(session_id, None)

    def get_character_name(self, session_id: str) -> Optional[str]:
        return self._names.get(session_id)

    def set_character_name(self, session_id: str, name: str) -> None:
        self._names[session_id] = name

    def get_story_append(self, session_id: str) -> bool:
        return self._story_append.get(session_id, self.config.enable_story_append)

    def set_story_append(self, session_id: str, enabled: bool) -> None:
        self._story_append[session_id] = enabled


store = SessionStore()
