"""Configuration management for lonely-world."""

import os
import sys
from getpass import getpass
from pathlib import Path

from lonely_world.models import GameConfig

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "local" / "data"
CONFIG_FILE = DATA_DIR / "config.json"


def _migrate_data_to_local() -> None:
    """Migrate old data/ directory to local/data/ if present."""
    old_data = BASE_DIR / "data"
    if old_data.exists() and old_data.is_dir() and not DATA_DIR.exists():
        import shutil

        DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_data), str(DATA_DIR))


DEFAULT_MODEL = "gpt-5-mini"
_KEYRING_SERVICE = "lonely-world"
_KEYRING_USERNAME = "api_key"


def ensure_dirs() -> None:
    _migrate_data_to_local()
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    import json

    try:
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: dict) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_keyring_api_key() -> str:
    try:
        import keyring

        value = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        return value or ""
    except Exception:
        return ""


def _set_keyring_api_key(key: str) -> bool:
    try:
        import keyring

        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, key)
        return True
    except Exception:
        return False


def load_config() -> GameConfig:
    ensure_dirs()
    raw = _read_json(CONFIG_FILE, {})
    return GameConfig.from_dict(raw)


def save_config(cfg: GameConfig) -> None:
    _write_json(CONFIG_FILE, cfg.to_dict())


def ensure_config(cfg: GameConfig) -> GameConfig:
    env_key = os.getenv("OPENAI_API_KEY") or os.getenv("LONELY_WORLD_API_KEY")
    env_base = os.getenv("OPENAI_BASE_URL") or os.getenv("LONELY_WORLD_BASE_URL")
    env_model = os.getenv("LONELY_WORLD_MODEL")
    changed = False

    # API Key resolution: env > keyring > config file > prompt
    api_key = env_key or _get_keyring_api_key() or cfg.api_key
    if api_key:
        if cfg.api_key != api_key:
            cfg.api_key = api_key
            changed = True
    else:
        print("\n⚠️  安全提示：")
        print("  - 建议使用环境变量 OPENAI_API_KEY 或 LONELY_WORLD_API_KEY")
        print("  - 系统将优先尝试把 API Key 存入系统密钥环（keyring）")
        print("  - 若密钥环不可用，才会明文存储到本地 local/data/config.json")
        print("  - 请勿在公共计算机上保存密钥\n")
        key = getpass("请输入大模型 API Key（输入时不可见）: ").strip()
        if key:
            cfg.api_key = key
            changed = True
            if _set_keyring_api_key(key):
                print("✓ API Key 已保存到系统密钥环")
                # Clear from config file since keyring succeeded
                cfg.api_key = ""
                changed = True
            else:
                print("⚠️  密钥环不可用，API Key 已保存到本地配置文件")
        else:
            print("未配置 API Key，无法继续。")
            sys.exit(1)

    # Migration: if api_key exists in config file and keyring is empty, move it to keyring
    if cfg.api_key and not _get_keyring_api_key():
        if _set_keyring_api_key(cfg.api_key):
            cfg.api_key = ""
            changed = True

    if env_base:
        if cfg.base_url != env_base:
            cfg.base_url = env_base
            changed = True
    elif not cfg.base_url:
        while True:
            base_url = input("请输入 API Base URL: ").strip()
            if base_url:
                cfg.base_url = base_url
                changed = True
                break
            print("Base URL 不能为空。")

    if env_model:
        if cfg.model != env_model:
            cfg.model = env_model
            changed = True
    elif not cfg.model:
        while True:
            model_input = input(f"请输入模型名称 (例如 {DEFAULT_MODEL}): ").strip()
            if model_input:
                cfg.model = model_input
                changed = True
                break
            print("模型名称不能为空。")

    if changed:
        save_config(cfg)
    return cfg
