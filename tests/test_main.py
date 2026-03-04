"""Tests for lonely-world."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestUtilityFunctions:
    """Test utility functions from main module."""

    def test_now_ts(self):
        """Test timestamp generation."""
        from main import now_ts

        ts = now_ts()
        assert isinstance(ts, str)
        assert len(ts) > 0
        assert "T" in ts

    def test_safe_name_normal(self):
        """Test safe_name with normal input."""
        from main import safe_name

        assert safe_name("测试角色") == "测试角色"
        assert safe_name("  角色名  ") == "角色名"

    def test_safe_name_special_chars(self):
        """Test safe_name with special characters."""
        from main import safe_name

        assert safe_name("角色/名字") == "角色_名字"
        assert safe_name("角色\\名字") == "角色_名字"
        assert safe_name("角色:名字") == "角色_名字"
        assert safe_name('角色"名字') == "角色_名字"
        assert safe_name("角色<名字>") == "角色_名字_"
        assert safe_name("角色|名字") == "角色_名字"
        assert safe_name("角色?名字") == "角色_名字"
        assert safe_name("角色*名字") == "角色_名字"

    def test_safe_name_empty(self):
        """Test safe_name with empty input."""
        from main import safe_name

        assert safe_name("") == "无名"
        assert safe_name("   ") == "无名"


class TestJSONOperations:
    """Test JSON read/write operations."""

    def test_read_json_nonexistent(self, tmp_path: Path):
        """Test reading non-existent JSON file."""
        from main import read_json

        result = read_json(tmp_path / "nonexistent.json", {"default": "value"})
        assert result == {"default": "value"}

    def test_write_and_read_json(self, tmp_path: Path):
        """Test writing and reading JSON file."""
        from main import read_json, write_json

        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42, "nested": {"a": 1}}

        write_json(test_file, test_data)
        assert test_file.exists()

        result = read_json(test_file, {})
        assert result == test_data

    def test_read_json_invalid(self, tmp_path: Path):
        """Test reading invalid JSON file."""
        from main import read_json

        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json {", encoding="utf-8")

        result = read_json(test_file, {"default": True})
        assert result == {"default": True}


class TestCharacterOperations:
    """Test character-related operations."""

    def test_create_character(self):
        """Test character creation."""
        from main import create_character

        character = create_character("测试角色")

        assert character["name"] == "测试角色"
        assert "created_at" in character
        assert "updated_at" in character
        assert "world" in character
        assert "state" in character
        assert character["state"]["items"] == []
        assert character["state"]["skills"] == []
        assert character["conversation"] == []

    def test_character_paths(self):
        """Test character path generation."""
        from main import (
            character_dir,
            character_json_path,
            character_story_path,
            safe_name,
        )

        name = "测试角色"
        safe = safe_name(name)

        char_dir = character_dir(name)
        json_path = character_json_path(name)
        story_path = character_story_path(name)

        assert safe in str(char_dir)
        assert str(json_path).endswith("character.json")
        assert str(story_path).endswith("story.md")


class TestStoryOperations:
    """Test story-related operations."""

    def test_append_story(self, tmp_path: Path):
        """Test appending to story file."""
        from main import append_story

        story_file = tmp_path / "story.md"

        append_story(story_file, "测试角色", "第一段故事")
        assert story_file.exists()

        content = story_file.read_text(encoding="utf-8")
        assert "测试角色" in content
        assert "第一段故事" in content

        append_story(story_file, "测试角色", "第二段故事")
        content = story_file.read_text(encoding="utf-8")
        assert "第二段故事" in content

    def test_read_story_tail(self, tmp_path: Path):
        """Test reading story tail."""
        from main import read_story_tail

        story_file = tmp_path / "story.md"
        long_content = "A" * 2000
        story_file.write_text(long_content, encoding="utf-8")

        tail = read_story_tail(story_file, max_chars=500)
        assert len(tail) == 500
        assert tail == "A" * 500

    def test_read_story_tail_nonexistent(self, tmp_path: Path):
        """Test reading tail of non-existent story."""
        from main import read_story_tail

        story_file = tmp_path / "nonexistent.md"
        tail = read_story_tail(story_file)
        assert tail == ""


class TestParseJSON:
    """Test JSON parsing from text."""

    def test_parse_json_valid(self):
        """Test parsing valid JSON."""
        from main import parse_json

        text = '{"key": "value", "number": 42}'
        result = parse_json(text)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_surrounding_text(self):
        """Test parsing JSON with surrounding text."""
        from main import parse_json

        text = 'Some text before {"key": "value"} some text after'
        result = parse_json(text)

        assert result == {"key": "value"}

    def test_parse_json_invalid(self):
        """Test parsing invalid JSON."""
        from main import parse_json

        text = "not json at all"
        result = parse_json(text)

        assert result is None


class TestExportOperations:
    """Test export functionality."""

    def test_export_story(self, tmp_path: Path):
        """Test story export."""
        from main import export_story

        story_file = tmp_path / "story.md"
        story_file.write_text("# 测试故事\n\n内容", encoding="utf-8")

        export_dir = tmp_path / "export"
        export_dir.mkdir()

        export_path = export_story(story_file, export_dir)

        assert export_path is not None
        assert export_path.exists()
        assert export_path.read_text(encoding="utf-8") == "# 测试故事\n\n内容"

    def test_export_story_nonexistent(self, tmp_path: Path):
        """Test exporting non-existent story."""
        from main import export_story

        story_file = tmp_path / "nonexistent.md"
        export_dir = tmp_path / "export"
        export_dir.mkdir()

        export_path = export_story(story_file, export_dir)

        assert export_path is None

    def test_export_role_summary(self, tmp_path: Path):
        """Test role summary export."""
        from main import export_role_summary

        character = {
            "name": "测试角色",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "world": {"time": "古代", "place": "中国"},
            "state": {"items": ["剑"], "skills": ["武艺"]},
            "memory_summary": "测试记忆",
            "world_qa": [],
            "conversation": [],
        }

        export_dir = tmp_path / "export"
        export_dir.mkdir()

        export_path = export_role_summary(character, export_dir)

        assert export_path.exists()
        content = export_path.read_text(encoding="utf-8")
        assert "测试角色" in content
        assert "古代" in content
        assert "剑" in content


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()
    return client


class TestAPIIntegration:
    """Test API integration (mocked)."""

    @patch("main.OpenAI")
    def test_get_client_with_base_url(self, mock_openai):
        """Test client creation with base URL."""
        from main import get_client

        cfg = {"api_key": "test-key", "base_url": "https://api.example.com/v1"}

        get_client(cfg)

        mock_openai.assert_called_once_with(
            api_key="test-key", base_url="https://api.example.com/v1"
        )

    @patch("main.OpenAI")
    def test_get_client_without_base_url(self, mock_openai):
        """Test client creation without base URL."""
        from main import get_client

        cfg = {"api_key": "test-key"}

        get_client(cfg)

        mock_openai.assert_called_once_with(api_key="test-key")
