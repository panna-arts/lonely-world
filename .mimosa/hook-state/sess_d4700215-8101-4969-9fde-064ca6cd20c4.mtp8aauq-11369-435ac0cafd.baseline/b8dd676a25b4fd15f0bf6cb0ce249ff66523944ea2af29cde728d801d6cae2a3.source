"""Tests for game loop logic."""

import builtins
from pathlib import Path
from unittest.mock import MagicMock, patch

from lonely_world.game.engine import GameEngine
from lonely_world.game.loop import _handle_special_command
from lonely_world.models import Character, CharacterState, World


class TestHandleSpecialCommand:
    def setup_method(self):
        self.char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )

    def _make_engine(self, char, tmp_path, story_text=None):
        story = tmp_path / "story.md"
        if story_text is not None:
            story.write_text(story_text, encoding="utf-8")
        export_story = tmp_path / "es"
        export_char = tmp_path / "ec"
        export_story.mkdir(exist_ok=True)
        export_char.mkdir(exist_ok=True)
        mock_client = MagicMock()
        return GameEngine(
            mock_client, char, tmp_path / "char.json", story, export_story, export_char
        )

    def test_story_command(self, tmp_path: Path, capsys):
        engine = self._make_engine(self.char, tmp_path, "# 故事\n\n内容")
        result = _handle_special_command(engine, "故事")
        assert result is True
        captured = capsys.readouterr()
        assert "内容" in captured.out or "内容" in captured.err

    def test_help_command(self, tmp_path: Path, capsys):
        engine = self._make_engine(self.char, tmp_path)
        result = _handle_special_command(engine, "help")
        assert result is True
        captured = capsys.readouterr()
        assert "可用命令" in captured.out or "可用命令" in captured.err

    def test_export_story_command(self, tmp_path: Path):
        engine = self._make_engine(self.char, tmp_path, "# 测试\n\n内容")
        result = _handle_special_command(engine, "export")
        assert result is True
        assert any(engine.export_story_dir.iterdir())

    def test_export_role_command(self, tmp_path: Path):
        engine = self._make_engine(self.char, tmp_path)
        result = _handle_special_command(engine, "export-role")
        assert result is True
        assert any(engine.export_character_dir.iterdir())

    def test_unknown_command(self, tmp_path: Path):
        engine = self._make_engine(self.char, tmp_path)
        result = _handle_special_command(engine, "hello")
        assert result is False


class TestPlayLoop:
    @patch.object(builtins, "input", side_effect=["你好", "退出"])
    def test_basic_loop(self, mock_input, tmp_path: Path):
        from lonely_world.game.loop import play_loop

        mock_client = MagicMock()
        mock_client.chat_json.return_value = {"reply": "回复"}
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        json_path = tmp_path / "char.json"
        story_path = tmp_path / "story.md"
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()

        play_loop(mock_client, char, json_path, story_path, es, ec, enable_story_append=False)
        assert char.conversation[0].content == "你好"
        assert char.conversation[1].content == "回复"
        assert json_path.exists()

    @patch.object(builtins, "input", side_effect=["故事", "退出"])
    def test_story_command_in_loop(self, mock_input, tmp_path: Path, capsys):
        from lonely_world.game.loop import play_loop

        mock_client = MagicMock()
        story_path = tmp_path / "story.md"
        story_path.write_text("# 故事\n\n片段", encoding="utf-8")
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()

        play_loop(
            mock_client, char, tmp_path / "char.json", story_path, es, ec, enable_story_append=False
        )
        captured = capsys.readouterr()
        assert "片段" in captured.out or "片段" in captured.err

    @patch.object(builtins, "input", side_effect=["你好", "退出"])
    def test_story_append_enabled(self, mock_input, tmp_path: Path):
        from lonely_world.game.loop import play_loop

        mock_client = MagicMock()
        mock_client.chat_json.return_value = {"reply": "回复"}
        mock_client.chat_text.return_value = "文学续写内容"
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        json_path = tmp_path / "char.json"
        story_path = tmp_path / "story.md"
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()

        play_loop(mock_client, char, json_path, story_path, es, ec, enable_story_append=True)
        assert story_path.exists()
        text = story_path.read_text(encoding="utf-8")
        assert "文学续写内容" in text

    @patch.object(builtins, "input", side_effect=["你好", "undo", "退出"])
    def test_undo_command(self, mock_input, tmp_path: Path):
        from lonely_world.game.loop import play_loop

        mock_client = MagicMock()
        mock_client.chat_json.return_value = {"reply": "回复"}
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        json_path = tmp_path / "char.json"
        story_path = tmp_path / "story.md"
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()

        play_loop(mock_client, char, json_path, story_path, es, ec, enable_story_append=False)
        # After undo, the conversation should be empty (reverted to state before "你好")
        assert len(char.conversation) == 0
        assert json_path.exists()
