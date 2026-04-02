"""Tests for GameEngine."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from lonely_world.game.engine import GameEngine, TurnResult
from lonely_world.models import Character, CharacterState, World


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
