"""File storage operations for lonely-world."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from lonely_world.models import Character

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "local" / "data"
CHAR_DIR = DATA_DIR / "characters"


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_name(name: str) -> str:
    cleaned = name.strip()
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        cleaned = cleaned.replace(ch, "_")
    return cleaned or "无名"


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_storage_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHAR_DIR.mkdir(parents=True, exist_ok=True)


def legacy_character_path(name: str) -> Path:
    return CHAR_DIR / f"{safe_name(name)}.json"


def character_dir(name: str) -> Path:
    return CHAR_DIR / safe_name(name)


def character_json_path(name: str) -> Path:
    return character_dir(name) / "character.json"


def character_story_path(name: str) -> Path:
    return character_dir(name) / "story.md"


def character_export_dir(name: str) -> Path:
    return character_dir(name) / "expert"


def character_export_story_dir(name: str) -> Path:
    return character_export_dir(name) / "story"


def character_export_character_dir(name: str) -> Path:
    return character_export_dir(name) / "characters"


def list_characters() -> list[str]:
    ensure_storage_dirs()
    names = []
    for path in CHAR_DIR.iterdir():
        if path.is_dir() and (path / "character.json").exists():
            names.append(path.name)
        elif path.is_file() and path.suffix == ".json":
            names.append(path.stem)
    return sorted(names)


def prepare_character_storage(name: str) -> dict[str, Path]:
    legacy_path = legacy_character_path(name)
    char_dir = character_dir(name)
    json_path = character_json_path(name)
    story_path = character_story_path(name)
    export_story_dir = character_export_story_dir(name)
    export_character_dir = character_export_character_dir(name)

    if legacy_path.exists():
        char_dir.mkdir(parents=True, exist_ok=True)
        if json_path.exists():
            backup = char_dir / f"legacy_{now_ts().replace(':', '-')}.json"
            legacy_path.rename(backup)
        else:
            legacy_path.rename(json_path)

    export_story_dir.mkdir(parents=True, exist_ok=True)
    export_character_dir.mkdir(parents=True, exist_ok=True)

    return {
        "dir": char_dir,
        "json": json_path,
        "story": story_path,
        "export_story_dir": export_story_dir,
        "export_character_dir": export_character_dir,
    }


def load_character(name: str) -> Optional[Character]:
    json_path = character_json_path(name)
    if not json_path.exists():
        return None
    raw = _read_json(json_path, {})
    if not raw:
        return None
    return Character.from_dict(raw)


def save_character(character: Character, json_path: Path) -> None:
    character.updated_at = now_ts()
    _write_json(json_path, character.to_dict())


def delete_character(name: str) -> bool:
    char_dir = character_dir(name)
    legacy_path = legacy_character_path(name)
    removed = False
    if char_dir.exists():
        import shutil

        shutil.rmtree(char_dir)
        removed = True
    if legacy_path.exists():
        legacy_path.unlink()
        removed = True
    return removed


def rename_character(old_name: str, new_name: str) -> bool:
    old_dir = character_dir(old_name)
    new_dir = character_dir(new_name)
    old_legacy = legacy_character_path(old_name)
    if old_dir.exists():
        if new_dir.exists():
            return False
        old_dir.rename(new_dir)
        return True
    if old_legacy.exists():
        if new_dir.exists() or character_json_path(new_name).exists():
            return False
        old_legacy.rename(character_json_path(new_name))
        return True
    return False


def read_story_tail(path: Path, max_chars: int = 1200) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[-max_chars:] if len(text) > max_chars else text


def append_story(path: Path, title: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# 故事：{title}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n\n#### {now_ts()}\n\n{content.strip()}\n")


def export_story(story_path: Path, export_dir: Path) -> Optional[Path]:
    if not story_path.exists():
        return None
    ts = now_ts().replace(":", "-")
    export_path = export_dir / f"story_export_{ts}.md"
    export_path.write_text(story_path.read_text(encoding="utf-8"), encoding="utf-8")
    return export_path


def export_role_summary(character: Character, export_dir: Path) -> Path:
    ts = now_ts().replace(":", "-")
    name = character.name or "无名"
    export_path = export_dir / f"character_export_{safe_name(name)}_{ts}.md"

    full_json = json.dumps(character.to_dict(), ensure_ascii=False, indent=2)
    world_json = json.dumps(character.world.to_dict(), ensure_ascii=False, indent=2)
    state_json = json.dumps(character.state.to_dict(), ensure_ascii=False, indent=2)
    world_qa_json = json.dumps(character.world_qa, ensure_ascii=False, indent=2)
    conversation_json = json.dumps(
        [m.to_dict() for m in character.conversation], ensure_ascii=False, indent=2
    )

    lines = [
        f"# 角色导出：{name}",
        "",
        f"- 导出时间：{now_ts()}",
        "",
        "## 基本信息",
        f"- 角色名称：{name}",
        f"- 创建时间：{character.created_at}",
        f"- 更新时间：{character.updated_at}",
        "",
        "## 世界观",
        "```json",
        world_json,
        "```",
        "",
        "## 角色状态",
        "```json",
        state_json,
        "```",
        "",
        "## 长期记忆摘要",
        character.memory_summary,
        "",
        "## 世界观问答",
        "```json",
        world_qa_json,
        "```",
        "",
        "## 对话记录",
        "```json",
        conversation_json,
        "```",
        "",
        "## 完整 JSON",
        "```json",
        full_json,
        "```",
    ]

    export_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return export_path
