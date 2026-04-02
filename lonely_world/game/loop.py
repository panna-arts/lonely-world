"""Main game loop (CLI adapter)."""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from lonely_world.game import memory
from lonely_world.game.engine import GameEngine
from lonely_world.llm.base import LLMProvider
from lonely_world.models import Character
from lonely_world.storage import save_character

logger = logging.getLogger(__name__)
console = Console()


def show_recent_conversation(character: Character, limit_pairs: int = 6) -> None:
    records = [m for m in character.conversation if m.role in ("user", "assistant")]
    if not records:
        return
    console.print("\n[dim]上次对话回顾：[/dim]")
    tail = records[-limit_pairs * 2 :]
    for msg in tail:
        role = "你" if msg.role == "user" else character.name
        console.print(f"[dim]{role}：{msg.content}[/dim]")
    console.print("")


def _show_help() -> None:
    lines = [
        "[bold cyan]游戏内可用命令[/bold cyan]",
        "",
        "  [green]help / ?[/green]        显示本帮助信息",
        "  [green]undo / 撤回[/green]      撤销上一轮输入并恢复状态",
        "  [green]story / 故事[/green]     查看 story.md 最近片段",
        "  [green]export / 导出故事[/green] 导出故事副本",
        "  [green]export-role / 导出角色[/green] 导出角色汇总信息",
        "  [green]quit / 退出[/green]      保存并结束游戏",
    ]
    console.print(Panel("\n".join(lines), title="lonely-world", border_style="cyan"))


def _handle_special_command(
    engine: GameEngine,
    user_input: str,
) -> bool:
    lower_input = user_input.lower()
    if lower_input in {"help", "?", "/help"}:
        _show_help()
        return True
    if lower_input in {"故事", "/story", "story"}:
        story_tail = engine.read_story_tail(1200)
        if story_tail:
            console.print(Panel(story_tail, title="故事摘要", border_style="magenta"))
        else:
            console.print("[dim]暂无故事内容。[/dim]")
        return True
    if lower_input in {"导出故事", "/export", "export"}:
        export_path = engine.export_story_file()
        if export_path:
            console.print(f"[green]故事已导出：{export_path}[/green]")
        else:
            console.print("[dim]暂无故事可导出。[/dim]")
        return True
    if lower_input in {"导出角色", "/export-role", "export-role"}:
        export_path = engine.export_role_file()
        console.print(f"[green]角色已导出：{export_path}[/green]")
        return True
    return False


def play_loop(
    client: LLMProvider,
    character: Character,
    json_path: Path,
    story_path: Path,
    export_story_dir: Path,
    export_character_dir: Path,
    enable_story_append: bool = False,
) -> None:
    engine = GameEngine(
        client=client,
        character=character,
        json_path=json_path,
        story_path=story_path,
        export_story_dir=export_story_dir,
        export_character_dir=export_character_dir,
        enable_story_append=enable_story_append,
    )

    console.print(
        Panel(
            "输入 [bold cyan]help[/bold cyan] 查看可用命令，"
            "[bold cyan]quit[/bold cyan] 保存并退出。",
            title="进入游戏",
            border_style="green",
        )
    )

    while True:
        user_input = console.input("[bold]你：[/bold]").strip()
        if not user_input:
            continue
        lower_input = user_input.lower()
        if lower_input in {"退出", "quit", "exit"}:
            save_character(character, json_path)
            console.print("[green]已保存，期待下次继续。[/green]")
            return

        if lower_input in {"undo", "撤回", "/undo"}:
            if engine.undo():
                console.print("[yellow]已撤回上一轮操作。[/yellow]")
            else:
                console.print("[dim]没有可撤回的操作。[/dim]")
            continue

        if _handle_special_command(engine, user_input):
            continue

        engine.snapshot()

        try:
            with console.status("[bold cyan]正在整理记忆…[/bold cyan]"):
                compressed = memory.maybe_compress_memory(character, client, character.name)
            if compressed:
                console.print("[dim]（已自动归档早期对话到长期记忆）[/dim]")
        except Exception as exc:
            logger.warning("Memory compression check failed: %s", exc)

        try:
            with console.status("[bold green]正在构思故事…[/bold green]"):
                result = engine.process_turn(user_input)
        except Exception as exc:
            logger.exception("Turn processing failed")
            console.print(f"[red]⚠️  {exc}[/red]")
            continue

        if result.error:
            console.print(f"[red]⚠️  {result.error}[/red]")
            continue

        if result.story_appended:
            pass  # already handled in engine

        console.print(
            Panel(result.reply, title=f"[bold]{character.name}[/bold]", border_style="blue")
        )
