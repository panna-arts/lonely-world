"""Command-line interface for lonely-world."""

import argparse
import sys
from typing import Optional

from rich.console import Console

from lonely_world.config import ensure_config, load_config, save_config
from lonely_world.game.loop import play_loop, show_recent_conversation
from lonely_world.game.world import build_world
from lonely_world.llm.factory import create_provider
from lonely_world.logging_config import setup_logging
from lonely_world.models import Character, CharacterState, GameConfig, World
from lonely_world.storage import (
    delete_character,
    ensure_storage_dirs,
    list_characters,
    load_character,
    now_ts,
    prepare_character_storage,
    rename_character,
    save_character,
)

__version__ = "0.2.0"
console = Console()


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="lonely-world",
        description="一款中文命令行文字探险游戏",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="启用详细日志输出")
    parser.add_argument("--story-append", action="store_true", help="启用文学续写功能")
    parser.add_argument("--provider", type=str, default=None, help="指定 LLM 提供商")
    parser.add_argument("--model", type=str, default=None, help="指定模型名称")
    parser.add_argument("--delete-character", type=str, default=None, help="删除指定角色")
    return parser.parse_args(argv)


def _prompt_confirm(message: str) -> bool:
    while True:
        choice = input(f"{message} [y/N]: ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no", ""}:
            return False


def _manage_characters() -> Optional[str]:
    """Show character list and allow selection/deletion/rename. Returns selected name or None for new."""
    ensure_storage_dirs()
    chars = list_characters()
    if chars:
        console.print("")
        console.print("[bold cyan]已存在角色：[/bold cyan]")
        for idx, name in enumerate(chars, 1):
            console.print(f"  {idx}. {name}")
        console.print("  [dim]0. 创建新角色[/dim]")
        console.print("  [dim red]d. 删除角色[/dim red]")
        console.print("  [dim yellow]r. 重命名角色[/dim yellow]")
        while True:
            choice = input("\n请选择角色编号（或输入 d/r）：").strip()
            if not choice:
                continue
            if choice == "0":
                return None
            if choice.lower() == "d":
                name = input("请输入要删除的角色名称：").strip()
                if name and _prompt_confirm(f"确定要删除角色 '{name}' 吗？"):
                    if delete_character(name):
                        console.print(f"[green]角色 '{name}' 已删除。[/green]")
                    else:
                        console.print(f"[red]未找到角色 '{name}'。[/red]")
                continue
            if choice.lower() == "r":
                old_name = input("请输入要重命名的角色名称：").strip()
                if not old_name:
                    continue
                new_name = input("请输入新名称：").strip()
                if new_name:
                    if rename_character(old_name, new_name):
                        console.print(f"[green]角色 '{old_name}' 已重命名为 '{new_name}'。[/green]")
                    else:
                        console.print(
                            "[red]重命名失败，请检查角色是否存在或新名称是否已被占用。[/red]"
                        )
                continue
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(chars):
                    return chars[idx - 1]
                console.print("[red]编号无效，请重新选择。[/red]")
            else:
                return choice
    return None


def _apply_cli_overrides(cfg: GameConfig, args: argparse.Namespace) -> GameConfig:
    changed = False
    if args.provider and cfg.provider != args.provider:
        cfg.provider = args.provider
        changed = True
    if args.model and cfg.model != args.model:
        cfg.model = args.model
        changed = True
    if args.story_append and not cfg.enable_story_append:
        cfg.enable_story_append = True
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def main(argv: Optional[list] = None) -> None:
    args = _parse_args(argv)
    setup_logging(verbose=args.verbose)

    ensure_storage_dirs()
    cfg = load_config()
    cfg = ensure_config(cfg)
    cfg = _apply_cli_overrides(cfg, args)

    if args.delete_character:
        name = args.delete_character.strip()
        if name and _prompt_confirm(f"确定要删除角色 '{name}' 吗？"):
            if delete_character(name):
                console.print(f"[green]角色 '{name}' 已删除。[/green]")
            else:
                console.print(f"[red]未找到角色 '{name}'。[/red]")
        return

    client = create_provider(
        provider=cfg.provider,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        model=cfg.model,
    )

    selected = _manage_characters()
    if selected is None:
        name = input("请输入角色名称：").strip()
        if not name:
            console.print("[red]角色名称不能为空。[/red]")
            sys.exit(1)
    else:
        name = selected

    storage = prepare_character_storage(name)
    json_path = storage["json"]
    story_path = storage["story"]
    export_story_dir = storage["export_story_dir"]
    export_character_dir = storage["export_character_dir"]

    character = load_character(name)
    if character is not None:
        console.print(f"[green]已载入角色：{character.name}[/green]")
        show_recent_conversation(character)
    else:
        character = Character(
            name=name,
            created_at=now_ts(),
            updated_at=now_ts(),
            world=World(),
            state=CharacterState(),
        )
        world, qa = build_world(client)
        character.world = world
        character.world_qa = qa
        character.memory_summary = (
            f"世界观：时间={character.world.time}；"
            f"地点={character.world.place}；"
            f"人物={','.join(character.world.people)}。"
        )
        save_character(character, json_path)
        console.print("[green]\n世界观已建立，角色已创建并保存。[/green]")

    play_loop(
        client=client,
        character=character,
        json_path=json_path,
        story_path=story_path,
        export_story_dir=export_story_dir,
        export_character_dir=export_character_dir,
        enable_story_append=cfg.enable_story_append,
    )


if __name__ == "__main__":
    main()
