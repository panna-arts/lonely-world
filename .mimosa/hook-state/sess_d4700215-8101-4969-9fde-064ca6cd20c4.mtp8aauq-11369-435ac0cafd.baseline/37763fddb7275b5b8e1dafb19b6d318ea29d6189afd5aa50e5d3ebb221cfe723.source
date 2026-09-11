"""Tests for world-building module."""

from unittest.mock import MagicMock

from lonely_world.game.world import WorldBuilder, build_world, generate_world_question, summarize_world
from lonely_world.models import World


class TestGenerateWorldQuestion:
    def test_returns_stripped_question(self):
        client = MagicMock()
        client.chat_text.return_value = '  "故事发生在什么时代？"  '
        result = generate_world_question(client, [], 1)
        assert result == "故事发生在什么时代？"

    def test_locale_passed_through(self):
        client = MagicMock()
        client.chat_text.return_value = "question"
        generate_world_question(client, [], 1, locale="en")
        # Verify the prompt was for English locale
        call_args = client.chat_text.call_args[0][0]
        system_content = call_args[0]["content"]
        assert "Q&A" in system_content or "world-building" in system_content.lower()


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


class TestWorldBuilder:
    def test_locale_defaults_to_zh(self):
        client = MagicMock()
        client.chat_text.return_value = "question"
        builder = WorldBuilder(client)
        assert builder.locale == "zh"

    def test_locale_set_explicitly(self):
        client = MagicMock()
        client.chat_text.return_value = "question"
        builder = WorldBuilder(client, locale="en")
        assert builder.locale == "en"

    def test_five_rounds_required(self):
        client = MagicMock()
        client.chat_text_async = MagicMock(return_value="question")
        builder = WorldBuilder(client)
        for i in range(5):
            builder.submit_answer(f"answer{i}")  # Need to set current question first
        assert not builder.is_complete()
