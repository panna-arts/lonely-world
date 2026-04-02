"""UI-agnostic game engine for both CLI and Web."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from lonely_world.game import memory, prompts
from lonely_world.llm.base import LLMProvider
from lonely_world.llm.retry import _classify_error
from lonely_world.models import Character, CharacterState, ConversationRecord, World
from lonely_world.storage import (
    append_story,
    export_role_summary,
    export_story,
    now_ts,
    read_story_tail,
    save_character,
)


@dataclass
class TurnResult:
    """Result of processing a single game turn."""

    reply: str = ""
    memory_compressed: bool = False
    story_appended: bool = False
    state_updated: bool = False
    world_updated: bool = False
    memory_summary: str = ""
    error: str = ""


class GameEngine:
    """Core game logic without UI coupling."""

    def __init__(
        self,
        client: LLMProvider,
        character: Character,
        json_path: Path,
        story_path: Path,
        export_story_dir: Path,
        export_character_dir: Path,
        enable_story_append: bool = False,
    ) -> None:
        self.client = client
        self.character = character
        self.json_path = json_path
        self.story_path = story_path
        self.export_story_dir = export_story_dir
        self.export_character_dir = export_character_dir
        self.enable_story_append = enable_story_append
        self.history_stack: list[Character] = []

    def _build_game_messages(self, user_input: str) -> list[dict[str, str]]:
        recent = memory.select_conversation_context(
            self.character.conversation,
            user_input,
            budget=memory.DEFAULT_HISTORY_TOKEN_BUDGET,
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": prompts.game_system(self.character)}
        ]
        messages.extend(recent)
        messages.append({"role": "user", "content": user_input})
        return messages

    def _generate_story_append(self, user_input: str, assistant_reply: str) -> str:
        story_tail = read_story_tail(self.story_path, 1200)
        system = prompts.story_append_system()
        user = prompts.story_append_user(self.character, user_input, assistant_reply, story_tail)
        story = self.client.chat_text(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        return story.strip()

    async def _generate_story_append_async(self, user_input: str, assistant_reply: str) -> str:
        story_tail = read_story_tail(self.story_path, 1200)
        system = prompts.story_append_system()
        user = prompts.story_append_user(self.character, user_input, assistant_reply, story_tail)
        story = await self.client.chat_text_async(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        return story.strip()

    def snapshot(self) -> None:
        """Save a copy of current character state for undo."""
        self.history_stack.append(Character.from_dict(self.character.to_dict()))
        if len(self.history_stack) > 10:
            self.history_stack.pop(0)

    def undo(self) -> bool:
        """Restore character to previous snapshot."""
        if not self.history_stack:
            return False
        restored = self.history_stack.pop()
        for attr in (
            "name",
            "world",
            "state",
            "memory_summary",
            "world_qa",
            "conversation",
            "created_at",
            "updated_at",
        ):
            setattr(self.character, attr, getattr(restored, attr))
        save_character(self.character, self.json_path)
        return True

    def read_story_tail(self, max_chars: int = 1200) -> str:
        return read_story_tail(self.story_path, max_chars)

    def export_story_file(self) -> Optional[Path]:
        return export_story(self.story_path, self.export_story_dir)

    def export_role_file(self) -> Path:
        return export_role_summary(self.character, self.export_character_dir)

    def _apply_api_result(self, user_input: str, api_result: Any, result: TurnResult) -> str:
        reply = api_result.get("reply") if isinstance(api_result, dict) else None
        if not reply:
            reply = "（智能体没有返回有效内容，请重试。）"
        result.reply = reply

        self.character.conversation.append(
            ConversationRecord(role="user", content=user_input, ts=now_ts())
        )
        self.character.conversation.append(
            ConversationRecord(role="assistant", content=reply, ts=now_ts())
        )

        if isinstance(api_result, dict):
            state_dict = api_result.get("character_state")
            if state_dict is not None:
                self.character.state = CharacterState.from_dict(state_dict)
                result.state_updated = True
            world_dict = api_result.get("world_state")
            if world_dict is not None:
                self.character.world = World.from_dict(world_dict)
                result.world_updated = True
            if api_result.get("memory_summary"):
                self.character.memory_summary = api_result["memory_summary"]
                result.memory_summary = self.character.memory_summary

        return reply

    def _maybe_append_story(self, user_input: str, reply: str, result: TurnResult) -> None:
        if not self.enable_story_append:
            return
        try:
            story_append = self._generate_story_append(user_input, reply)
            if story_append:
                append_story(self.story_path, self.character.name or "无名", story_append)
                result.story_appended = True
        except Exception:
            pass  # non-fatal

    async def _maybe_append_story_async(
        self, user_input: str, reply: str, result: TurnResult
    ) -> None:
        if not self.enable_story_append:
            return
        try:
            story_append = await self._generate_story_append_async(user_input, reply)
            if story_append:
                append_story(self.story_path, self.character.name or "无名", story_append)
                result.story_appended = True
        except Exception:
            pass  # non-fatal

    def maybe_compress_memory(self) -> bool:
        """Compress conversation history if threshold is met."""
        try:
            return memory.maybe_compress_memory(self.character, self.client, self.character.name)
        except Exception:
            return False

    def process_turn(self, user_input: str) -> TurnResult:
        """Synchronous turn processing (for CLI)."""
        result = TurnResult()

        try:
            messages = self._build_game_messages(user_input)
            api_result = self.client.chat_json(messages)
        except Exception as exc:
            result.error = _classify_error(exc)
            return result

        reply = self._apply_api_result(user_input, api_result, result)
        self._maybe_append_story(user_input, reply, result)
        save_character(self.character, self.json_path)
        return result

    async def process_turn_async(self, user_input: str) -> TurnResult:
        """Asynchronous turn processing (for Web)."""
        result = TurnResult()

        try:
            messages = self._build_game_messages(user_input)
            api_result = await self.client.chat_json_async(messages)
        except Exception as exc:
            result.error = _classify_error(exc)
            return result

        reply = self._apply_api_result(user_input, api_result, result)
        await self._maybe_append_story_async(user_input, reply, result)
        save_character(self.character, self.json_path)
        return result

    async def process_turn_stream(self, user_input: str):
        """Asynchronous streaming turn processing yielding event dicts."""
        result = TurnResult()

        yield {"type": "thinking"}

        try:
            messages = self._build_game_messages(user_input)
            api_result = await self.client.chat_json_async(messages)
        except Exception as exc:
            result.error = _classify_error(exc)
            yield {"type": "error", "message": result.error}
            return

        reply = self._apply_api_result(user_input, api_result, result)

        # Simulate typing by yielding chunks
        chunk_size = 4
        for i in range(0, len(reply), chunk_size):
            yield {"type": "chunk", "text": reply[i : i + chunk_size]}

        await self._maybe_append_story_async(user_input, reply, result)
        save_character(self.character, self.json_path)

        yield {
            "type": "done",
            "reply": reply,
            "state_updated": result.state_updated,
            "world_updated": result.world_updated,
            "memory_summary": result.memory_summary,
            "story_appended": result.story_appended,
        }
