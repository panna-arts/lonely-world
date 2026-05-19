"""Tests for GameEngine."""

from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from lonely_world.game.engine import GameEngine, TurnResult
from lonely_world.models import Character, CharacterState, World


class AsyncIteratorFixture:
    """Helper that wraps a list to behave as an async iterator."""

    def __init__(self, items: list[str]):
        self._items = items
        self._i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._i >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._i]
        self._i += 1
        return item


@pytest.fixture
def engine(tmp_path: Path):
    client = MagicMock()
    client.chat_json.return_value = {
        "reply": "回复内容",
        "character_state": {"items": ["剑"]},
        "world_state": {"place": "森林"},
    }
    client.chat_text.return_value = "文学续写"
    client.chat_json_async = AsyncMock(
        return_value={"reply": "异步回复", "character_state": {"items": ["盾"]}}
    )
    client.chat_text_async = AsyncMock(return_value="异步文学续写")
    client.chat_text_stream_async = AsyncMock(
        return_value=AsyncIteratorFixture(["异步", "流式", "响应"])
    )

    char = Character(
        name="测试角色",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        world=World(place="村庄"),
        state=CharacterState(),
    )
    (tmp_path / "es").mkdir(exist_ok=True)
    (tmp_path / "ec").mkdir(exist_ok=True)
    return GameEngine(
        client=client,
        character=char,
        json_path=tmp_path / "char.json",
        story_path=tmp_path / "story.md",
        export_story_dir=tmp_path / "es",
        export_character_dir=tmp_path / "ec",
        enable_story_append=False,
    )


class TestGameEngineSync:
    def test_process_turn(self, engine: GameEngine):
        result = engine.process_turn("你好")
        assert isinstance(result, TurnResult)
        assert result.reply == "回复内容"
        assert result.state_updated is True
        assert result.world_updated is True
        assert engine.character.conversation[0].content == "你好"
        assert engine.character.conversation[1].content == "回复内容"
        assert engine.json_path.exists()

    def test_undo(self, engine: GameEngine):
        engine.process_turn("你好")
        assert len(engine.character.conversation) == 2
        engine.snapshot()
        engine.process_turn("再见")
        assert len(engine.character.conversation) == 4
        success = engine.undo()
        assert success is True
        assert len(engine.character.conversation) == 2

    def test_undo_empty(self, engine: GameEngine):
        assert engine.undo() is False

    def test_snapshot_limit(self, engine: GameEngine):
        for _ in range(12):
            engine.snapshot()
        assert len(engine.history_stack) == 10

    def test_story_append(self, engine: GameEngine):
        engine.enable_story_append = True
        result = engine.process_turn("你好")
        assert result.story_appended is True
        assert engine.story_path.exists()

    def test_export_story_empty(self, engine: GameEngine):
        assert engine.export_story_file() is None

    def test_export_role(self, engine: GameEngine):
        path = engine.export_role_file()
        assert path.exists()

    def test_error_handling(self, engine: GameEngine):
        engine.client.chat_json.side_effect = Exception("ConnectionError")
        result = engine.process_turn("你好")
        assert result.error != ""


class TestGameEngineAsync:
    @pytest.mark.anyio
    async def test_process_turn_async(self, engine: GameEngine):
        result = await engine.process_turn_async("你好")
        assert result.reply == "异步回复"
        assert result.state_updated is True
        assert engine.character.conversation[0].content == "你好"

    @pytest.mark.anyio
    async def test_process_turn_stream(self, engine: GameEngine):
        events = []
        async for event in engine.process_turn_stream("你好"):
            events.append(event)
        assert events[0]["type"] == "thinking"
        assert events[-1]["type"] == "done"
        assert events[-1]["reply"] == "异步回复"

    @pytest.mark.anyio
    async def test_stream_error(self, engine: GameEngine):
        engine.client.chat_json_async.side_effect = Exception("Timeout")
        events = []
        async for event in engine.process_turn_stream("你好"):
            events.append(event)
        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "error"

    @pytest.mark.anyio
    async def test_process_turn_stream_text_real_streaming(self, engine: GameEngine):
        """Test real streaming via process_turn_stream_text (text-only prompt).

        chat_text_stream_async yields chunks that form a valid JSON response.
        """
        engine.client.chat_text_stream_async = AsyncMock(
            return_value=AsyncIteratorFixture([
                '{"reply": "异步',
                '流式',
                '响应",',
                ' "character_state": {"items": ["剑"]},',
                ' "world_state": {"place": "森林"},',
                ' "memory_summary": "",',
                ' "world_updated": false,',
                ' "state_updated": false}',
            ])
        )
        events = []
        async for event in engine.process_turn_stream_text("你好"):
            events.append(event)
        assert events[0]["type"] == "thinking"
        done = next(e for e in events if e["type"] == "done")
        assert done["reply"] == "异步流式响应"
        assert done["state_updated"] is True

    @pytest.mark.anyio
    async def test_stream_text_falls_back_to_reply(self, engine: GameEngine):
        """If parse_json returns None, check we still get an error."""
        engine.client.chat_text_stream_async = AsyncMock(
            return_value=AsyncIteratorFixture(["这不是有效的", "JSON数据"])
        )
        events = []
        async for event in engine.process_turn_stream_text("你好"):
            events.append(event)
        assert events[0]["type"] == "thinking"
        assert any(e["type"] == "error" for e in events)

    @pytest.mark.anyio
    async def test_stream_text_error(self, engine: GameEngine):
        engine.client.chat_text_stream_async = AsyncMock(
            side_effect=Exception("Connection reset")
        )
        events = []
        async for event in engine.process_turn_stream_text("你好"):
            events.append(event)
        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "error"
        assert "Connection reset" in events[1]["message"]


class TestNamedSaves:
    def test_save_and_load_named(self, engine: GameEngine):
        engine.process_turn("第一回合")
        engine.save_named("检查点1")
        engine.process_turn("第二回合")
        engine.process_turn("第三回合")
        assert len(engine.character.conversation) == 6
        success = engine.load_named("检查点1")
        assert success is True
        assert len(engine.character.conversation) == 2

    def test_load_nonexistent(self, engine: GameEngine):
        assert engine.load_named("不存在的存档") is False

    def test_list_named_saves(self, engine: GameEngine):
        engine.save_named("alpha")
        engine.save_named("beta")
        engine.save_named("gamma")
        assert engine.list_named_saves() == ["alpha", "beta", "gamma"]

    def test_delete_named(self, engine: GameEngine):
        engine.save_named("to_delete")
        assert "to_delete" in engine.list_named_saves()
        assert engine.delete_named("to_delete") is True
        assert "to_delete" not in engine.list_named_saves()
        assert engine.delete_named("to_delete") is False  # already gone

    def test_named_save_no_collision_with_undo(self, engine: GameEngine):
        engine.process_turn("回合1")
        engine.save_named("checkpoint")
        engine.process_turn("回合2")
        engine.undo()
        assert len(engine.character.conversation) == 2
        engine.load_named("checkpoint")
        assert len(engine.character.conversation) == 2  # checkpoint had 2 messages
