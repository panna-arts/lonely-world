"""Tests for web session storage."""

from lonely_world.models import Character, CharacterState, World
from lonely_world.web.storage import SessionStorage


def test_list_and_prepare(tmp_path, monkeypatch):
    # Override DATA_DIR to use tmp_path

    monkeypatch.setattr("lonely_world.web.storage.DATA_DIR", tmp_path / "data")
    storage = SessionStorage("sess-123")
    assert storage.list_characters() == []

    paths = storage.prepare_character_storage("李逍遥")
    assert paths["json"].parent.exists()
    assert paths["story"].parent.exists()

    char = Character(
        name="李逍遥",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        world=World(),
        state=CharacterState(),
    )
    storage.save_character(char, paths["json"])
    assert storage.list_characters() == ["李逍遥"]


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr("lonely_world.web.storage.DATA_DIR", tmp_path / "data")
    storage = SessionStorage("sess-456")
    paths = storage.prepare_character_storage("赵灵儿")
    char = Character(
        name="赵灵儿",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        world=World(),
        state=CharacterState(),
    )
    storage.save_character(char, paths["json"])

    loaded = storage.load_character("赵灵儿")
    assert loaded is not None
    assert loaded.name == "赵灵儿"


def test_delete_and_rename(tmp_path, monkeypatch):
    monkeypatch.setattr("lonely_world.web.storage.DATA_DIR", tmp_path / "data")
    storage = SessionStorage("sess-789")
    paths = storage.prepare_character_storage("林月如")
    char = Character(
        name="林月如",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        world=World(),
        state=CharacterState(),
    )
    storage.save_character(char, paths["json"])

    assert storage.delete_character("林月如") is True
    assert storage.load_character("林月如") is None

    storage.prepare_character_storage("阿奴")
    storage.save_character(
        Character(
            name="阿奴",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
            world=World(),
            state=CharacterState(),
        ),
        storage.prepare_character_storage("阿奴")["json"],
    )
    assert storage.rename_character("阿奴", "阿奴2") is True
    assert storage.load_character("阿奴") is None
    assert storage.load_character("阿奴2") is not None
