"""Session-aware storage for the Web UI."""

import shutil
from pathlib import Path
from typing import Optional

from lonely_world.models import Character
from lonely_world.storage import _read_json, safe_name, save_character

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "local" / "data"


class SessionStorage:
    """File storage scoped to a browser session."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.base_dir = DATA_DIR / "sessions" / session_id
        self.char_dir = self.base_dir / "characters"

    def ensure_dirs(self) -> None:
        self.char_dir.mkdir(parents=True, exist_ok=True)

    def _character_dir(self, name: str) -> Path:
        return self.char_dir / safe_name(name)

    def _json_path(self, name: str) -> Path:
        return self._character_dir(name) / "character.json"

    def _story_path(self, name: str) -> Path:
        return self._character_dir(name) / "story.md"

    def list_characters(self) -> list[str]:
        self.ensure_dirs()
        names = []
        for path in self.char_dir.iterdir():
            if path.is_dir() and (path / "character.json").exists():
                names.append(path.name)
        return sorted(names)

    def prepare_character_storage(self, name: str) -> dict[str, Path]:
        char_dir = self._character_dir(name)
        json_path = self._json_path(name)
        story_path = self._story_path(name)
        export_dir = char_dir / "expert"
        export_story_dir = export_dir / "story"
        export_character_dir = export_dir / "characters"
        for p in (char_dir, export_story_dir, export_character_dir):
            p.mkdir(parents=True, exist_ok=True)
        return {
            "dir": char_dir,
            "json": json_path,
            "story": story_path,
            "export_story_dir": export_story_dir,
            "export_character_dir": export_character_dir,
        }

    def load_character(self, name: str) -> Optional[Character]:
        json_path = self._json_path(name)
        if not json_path.exists():
            return None
        raw = _read_json(json_path, {})
        if not raw:
            return None
        return Character.from_dict(raw)

    def delete_character(self, name: str) -> bool:
        char_dir = self._character_dir(name)
        if char_dir.exists():
            shutil.rmtree(char_dir)
            return True
        return False

    def rename_character(self, old_name: str, new_name: str) -> bool:
        old_dir = self._character_dir(old_name)
        new_dir = self._character_dir(new_name)
        if not old_dir.exists() or new_dir.exists():
            return False
        old_dir.rename(new_dir)
        return True

    def save_character(self, character: Character, json_path: Path) -> None:
        save_character(character, json_path)
