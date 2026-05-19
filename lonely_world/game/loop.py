"""Main game loop (CLI adapter)."""

import logging
import threading
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from lonely_world.game import memory
from lonely_world.game.engine import GameEngine
from lonely_world.i18n import _
from lonely_world.llm.base import LLMProvider
from lonely_world.models import Character
from lonely_world.storage import save_character

logger = logging.getLogger(__name__)
console = Console()


def show_recent_conversation(character: Character, limit_pairs: int = 10) -> None:
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
        "  [green]help / ?[/green]              显示本帮助信息",
        "  [green]undo / 撤回[/green]            撤销上一轮输入并恢复状态",
        "  [green]save <名称> / 存档 <名称>[/green] 保存命名快照",
        "  [green]load <名称> / 读档 <名称>[/green] 加载命名快照",
        "  [green]saves / 存档列表[/green]        列出所有命名快照",
        "  [green]story / 故事[/green]            查看 story.md 最近片段",
        "  [green]export / 导出故事[/green]        导出故事副本",
        "  [green]export-role / 导出角色[/green]    导出角色汇总信息",
        "  [green]quit / 退出[/green]              保存并结束游戏",
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

    # Named save/load commands
    parts = user_input.split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in {"save", "存档"}:
        if not arg:
            console.print("[yellow]用法：save <名称>[/yellow]")
            return True
        engine.save_named(arg)
        console.print(f"[green]已存档：{arg}[/green]")
        return True

    if cmd in {"load", "读档"}:
        if not arg:
            console.print("[yellow]用法：load <名称>[/yellow]")
            return True
        if engine.load_named(arg):
            console.print(f"[green]已读档：{arg}[/green]")
        else:
            console.print(f"[dim]存档不存在：{arg}[/dim]")
        return True

    if cmd in {"saves", "存档列表"}:
        names = engine.list_named_saves()
        if not names:
            console.print("[dim]暂无命名存档。[/dim]")
        else:
            console.print(f"[dim]可用存档：{', '.join(names)}[/dim]")
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

        # Run memory compression in background thread
        compression_done = threading.Event()
        compression_result = [False]

        def background_compress() -> None:
            try:
                compression_result[0] = memory.maybe_compress_memory(
                    character, client, character.name
                )
            except Exception as exc:
                logger.warning("Memory compression check failed: %s", exc)
            finally:
                compression_done.set()

        compress_thread = threading.Thread(target=background_compress, daemon=True)
        compress_thread.start()

        try:
            with console.status("[bold green]正在构思故事…[/bold green]"):
                result = engine.process_turn(user_input)
        except Exception as exc:
            logger.exception("Turn processing failed")
            console.print(f"[red]⚠️  {exc}[/red]")
            compression_done.wait()
            continue
        finally:
            compression_done.wait()

        if compression_result[0]:
            console.print("[dim]（已自动归档早期对话到长期记忆）[/dim]")

        if result.error:
            console.print(f"[red]⚠️  {result.error}[/red]")
            continue

        if result.story_appended:
            pass  # already handled in engine

        console.print(
            Panel(result.reply, title=f"[bold]{character.name}[/bold]", border_style="blue")
        )
