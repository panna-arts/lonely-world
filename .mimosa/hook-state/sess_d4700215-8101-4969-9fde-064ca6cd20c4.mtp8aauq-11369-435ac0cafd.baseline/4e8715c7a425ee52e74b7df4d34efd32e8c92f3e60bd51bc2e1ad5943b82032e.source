"""Tests for CLI."""

from unittest.mock import MagicMock, patch

import pytest

from lonely_world.cli import _manage_characters, _parse_args, main


class TestParseArgs:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            _parse_args(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "lonely-world" in captured.out

    def test_defaults(self):
        args = _parse_args([])
        assert args.verbose is False
        assert args.story_append is False
        assert args.provider is None
        assert args.model is None
        assert args.delete_character is None


class TestManageCharacters:
    @patch("lonely_world.cli.list_characters", return_value=["角色A", "角色B"])
    @patch("lonely_world.cli.input", side_effect=["1"])
    def test_select_existing(self, mock_input, mock_list):
        result = _manage_characters()
        assert result == "角色A"

    @patch("lonely_world.cli.list_characters", return_value=[])
    @patch("lonely_world.cli.input", side_effect=[])
    def test_create_new_when_empty(self, mock_input, mock_list):
        result = _manage_characters()
        assert result is None

    @patch("lonely_world.cli.list_characters", return_value=["角色A"])
    @patch("lonely_world.cli.input", side_effect=["2", "1"])
    def test_invalid_then_valid(self, mock_input, mock_list):
        result = _manage_characters()
        assert result == "角色A"

    @patch("lonely_world.cli.list_characters", return_value=["角色A"])
    @patch("lonely_world.cli.input", side_effect=["d", "角色A", "y"])
    @patch("lonely_world.cli.delete_character", return_value=True)
    @patch("lonely_world.cli.console")
    def test_delete_character(self, mock_console, mock_delete, mock_input, mock_list):
        # After deletion, function loops back; provide "1" to select remaining
        with patch("lonely_world.cli.input", side_effect=["d", "角色A", "y", "1"]):
            result = _manage_characters()
        assert result == "角色A"
        mock_delete.assert_called_once_with("角色A")

    @patch("lonely_world.cli.list_characters", return_value=["角色A"])
    @patch("lonely_world.cli.rename_character", return_value=True)
    @patch("lonely_world.cli.console")
    def test_rename_character(self, mock_console, mock_rename, mock_list):
        with patch("lonely_world.cli.input", side_effect=["r", "角色A", "角色B", "1"]):
            result = _manage_characters()
        assert result == "角色A"
        mock_rename.assert_called_once_with("角色A", "角色B")


class TestMain:
    @patch("lonely_world.cli.load_config")
    @patch("lonely_world.cli.ensure_config")
    @patch("lonely_world.cli.create_provider")
    @patch("lonely_world.cli.build_world")
    @patch("lonely_world.cli.play_loop")
    @patch("lonely_world.cli._manage_characters", return_value=None)
    @patch("lonely_world.cli.prepare_character_storage")
    def test_new_character(
        self,
        mock_prep,
        mock_select,
        mock_play,
        mock_build_world,
        mock_create_provider,
        mock_ensure_config,
        mock_load_config,
        tmp_path,
    ):
        from lonely_world.models import GameConfig, World

        mock_load_config.return_value = GameConfig(
            api_key="k", base_url="https://api.example.com/v1", model="gpt-4"
        )
        mock_ensure_config.return_value = mock_load_config.return_value
        mock_client = MagicMock()
        mock_create_provider.return_value = mock_client
        mock_build_world.return_value = (World(time="古代", place="长安"), [])

        json_path = tmp_path / "char.json"
        story_path = tmp_path / "story.md"
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()
        mock_prep.return_value = {
            "json": json_path,
            "story": story_path,
            "export_story_dir": es,
            "export_character_dir": ec,
        }

        with patch("lonely_world.cli.input", side_effect=["新角色"]):
            main(["--story-append"])
        mock_play.assert_called_once()
        assert json_path.exists()

    @patch("lonely_world.cli.load_config")
    @patch("lonely_world.cli.ensure_config")
    @patch("lonely_world.cli.create_provider")
    @patch("lonely_world.cli.play_loop")
    @patch("lonely_world.cli._manage_characters", return_value="老角色")
    @patch("lonely_world.cli.prepare_character_storage")
    @patch("lonely_world.cli.load_character")
    def test_existing_character(
        self,
        mock_load_char,
        mock_prep,
        mock_select,
        mock_play,
        mock_create_provider,
        mock_ensure_config,
        mock_load_config,
        tmp_path,
    ):
        from lonely_world.models import Character, CharacterState, GameConfig, World

        mock_load_config.return_value = GameConfig(api_key="k", model="gpt-4")
        mock_ensure_config.return_value = mock_load_config.return_value
        mock_client = MagicMock()
        mock_create_provider.return_value = mock_client
        mock_char = Character(
            name="老角色", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        mock_load_char.return_value = mock_char

        json_path = tmp_path / "char.json"
        story_path = tmp_path / "story.md"
        es = tmp_path / "es"
        ec = tmp_path / "ec"
        es.mkdir()
        ec.mkdir()
        mock_prep.return_value = {
            "json": json_path,
            "story": story_path,
            "export_story_dir": es,
            "export_character_dir": ec,
        }

        main([])
        mock_play.assert_called_once()
        mock_load_char.assert_called_once_with("老角色")

    @patch("lonely_world.cli.load_config")
    @patch("lonely_world.cli.ensure_config")
    @patch("lonely_world.cli.delete_character", return_value=True)
    def test_delete_character_cli(self, mock_delete, mock_ensure_config, mock_load_config):
        mock_load_config.return_value = MagicMock()
        mock_ensure_config.return_value = mock_load_config.return_value
        with patch("lonely_world.cli.input", side_effect=["y"]):
            main(["--delete-character", "测试角色"])
        mock_delete.assert_called_once_with("测试角色")
