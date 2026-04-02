"""Tests for world-building module."""

from unittest.mock import MagicMock

from lonely_world.game.world import build_world, generate_world_question, summarize_world
from lonely_world.models import World


class TestGenerateWorldQuestion:
    def test_returns_stripped_question(self):
        client = MagicMock()
        client.chat_text.return_value = '  "故事发生在什么时代？"  '
        result = generate_world_question(client, [], 1)
        assert result == "故事发生在什么时代？"


class TestSummarizeWorld:
    def test_valid_json_parsed(self):
        client = MagicMock()
        client.chat_json.return_value = {
            "time": "古代",
            "place": "长安",
            "people": ["李白"],
            "rules": "江湖规矩",
            "tone": "武侠",
            "notes": ["note1"],
        }
        result = summarize_world(client, [])
        assert result.time == "古代"
        assert result.place == "长安"
        assert result.people == ["李白"]
        assert result.notes == ["note1"]

    def test_empty_json_defaults(self):
        client = MagicMock()
        client.chat_json.return_value = {}
        result = summarize_world(client, [])
        assert result == World()


class TestBuildWorld:
    def test_build_world(self, monkeypatch):
        from lonely_world.game import world as world_module

        client = MagicMock()
        client.chat_text.return_value = "问题"
        client.chat_json.return_value = {
            "time": "古代",
            "place": "长安",
            "people": ["李白"],
            "rules": "江湖",
            "tone": "武侠",
            "notes": [],
        }
        inputs = ["答案1", "答案2", "答案3", "答案4", "答案5"]
        monkeypatch.setattr(world_module.console, "input", lambda _: inputs.pop(0))
        world, qa = build_world(client)
        assert world.time == "古代"
        assert len(qa) == 5
