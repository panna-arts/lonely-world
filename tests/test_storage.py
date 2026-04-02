"""Tests for storage module."""

from pathlib import Path

from lonely_world.models import Character, CharacterState, World
from lonely_world.storage import (
    append_story,
    delete_character,
    export_role_summary,
    export_story,
    list_characters,
    load_character,
    prepare_character_storage,
    read_story_tail,
    rename_character,
    safe_name,
)


class TestSafeName:
    def test_normal(self):
        assert safe_name("测试角色") == "测试角色"
        assert safe_name("  角色名  ") == "角色名"

    def test_special_chars(self):
        assert safe_name("角色/名字") == "角色_名字"
        assert safe_name('角色"名字') == "角色_名字"
        assert safe_name("角色<名字>") == "角色_名字_"

    def test_empty(self):
        assert safe_name("") == "无名"
        assert safe_name("   ") == "无名"


class TestReadJson:
    def test_read_json_invalid(self, tmp_path: Path):
        from lonely_world.storage import _read_json

        bad = tmp_path / "bad.json"
        bad.write_text("not valid json {", encoding="utf-8")
        result = _read_json(bad, {"default": True})
        assert result == {"default": True}


class TestStoryOperations:
    def test_append_and_read(self, tmp_path: Path):
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
        story_file = tmp_path / "story.md"
        story_file.write_text("A" * 2000, encoding="utf-8")
        tail = read_story_tail(story_file, max_chars=500)
        assert len(tail) == 500
        assert tail == "A" * 500

    def test_read_story_tail_nonexistent(self, tmp_path: Path):
        assert read_story_tail(tmp_path / "none.md") == ""


class TestExportOperations:
    def test_export_story(self, tmp_path: Path):
        story_file = tmp_path / "story.md"
        story_file.write_text("# 测试\n\n内容", encoding="utf-8")
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        result = export_story(story_file, export_dir)
        assert result is not None
        assert result.read_text(encoding="utf-8") == "# 测试\n\n内容"

    def test_export_story_nonexistent(self, tmp_path: Path):
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        assert export_story(tmp_path / "none.md", export_dir) is None

    def test_export_role_summary(self, tmp_path: Path):
        char = Character(
            name="测试",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-02T00:00:00",
            world=World(time="古代"),
            state=CharacterState(items=["剑"]),
        )
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        result = export_role_summary(char, export_dir)
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "测试" in text
        assert "古代" in text
        assert "剑" in text


class TestCharacterPaths:
    def test_paths(self):
        from lonely_world.storage import (
            character_dir,
            character_export_character_dir,
            character_export_dir,
            character_export_story_dir,
            character_json_path,
            character_story_path,
        )

        assert "hero" in str(character_dir("hero"))
        assert "story.md" in str(character_story_path("hero"))
        assert "expert" in str(character_export_dir("hero"))
        assert "story" in str(character_export_story_dir("hero"))
        assert "characters" in str(character_export_character_dir("hero"))
        assert "character.json" in str(character_json_path("hero"))


class TestListCharacters:
    def test_list_characters(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        # new style
        (tmp_path / "char1").mkdir()
        (tmp_path / "char1" / "character.json").write_text("{}", encoding="utf-8")
        # legacy style
        (tmp_path / "char2.json").write_text("{}", encoding="utf-8")
        names = list_characters()
        assert "char1" in names
        assert "char2" in names


class TestPrepareCharacterStorage:
    def test_legacy_migration_to_new_dir(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        # Create legacy file
        legacy = tmp_path / "hero.json"
        legacy.write_text('{"name": "hero"}', encoding="utf-8")
        storage = prepare_character_storage("hero")
        assert not legacy.exists()
        assert storage["json"].exists()
        data = storage_module._read_json(storage["json"], {})
        assert data.get("name") == "hero"

    def test_legacy_migration_with_existing_json(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        legacy = tmp_path / "hero.json"
        legacy.write_text('{"name": "legacy"}', encoding="utf-8")
        char_dir = tmp_path / "hero"
        char_dir.mkdir()
        (char_dir / "character.json").write_text('{"name": "existing"}', encoding="utf-8")
        storage = prepare_character_storage("hero")
        # Legacy file should be backed up, not overwrite existing json
        backups = list(char_dir.glob("legacy_*.json"))
        assert len(backups) == 1
        current = storage_module._read_json(storage["json"], {})
        assert current.get("name") == "existing"


class TestLoadCharacter:
    def test_load_nonexistent(self):
        from lonely_world.storage import load_character

        assert load_character("nobody") is None

    def test_load_empty_json(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        char_dir = tmp_path / "hero"
        char_dir.mkdir()
        (char_dir / "character.json").write_text("", encoding="utf-8")
        assert load_character("hero") is None


class TestDeleteCharacter:
    def test_delete_new_style(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        char_dir = tmp_path / "hero"
        char_dir.mkdir()
        (char_dir / "character.json").write_text("{}", encoding="utf-8")
        assert delete_character("hero") is True
        assert not char_dir.exists()

    def test_delete_legacy(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        legacy = tmp_path / "hero.json"
        legacy.write_text("{}", encoding="utf-8")
        assert delete_character("hero") is True
        assert not legacy.exists()

    def test_delete_nonexistent(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        assert delete_character("nobody") is False


class TestRenameCharacter:
    def test_rename_new_style(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        old_dir = tmp_path / "old_hero"
        old_dir.mkdir()
        (old_dir / "character.json").write_text("{}", encoding="utf-8")
        assert rename_character("old_hero", "new_hero") is True
        assert not old_dir.exists()
        assert (tmp_path / "new_hero").exists()

    def test_rename_target_exists(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "character.json").write_text("{}", encoding="utf-8")
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "character.json").write_text("{}", encoding="utf-8")
        assert rename_character("a", "b") is False

    def test_rename_nonexistent(self, monkeypatch, tmp_path: Path):
        from lonely_world import storage as storage_module

        monkeypatch.setattr(storage_module, "CHAR_DIR", tmp_path)
        assert rename_character("nobody", "somebody") is False
