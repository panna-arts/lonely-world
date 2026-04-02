"""World-building logic."""

from rich.console import Console

from lonely_world.game import prompts
from lonely_world.llm.base import LLMProvider
from lonely_world.models import World

console = Console()


def generate_world_question(client: LLMProvider, qa: list, round_index: int) -> str:
    system, user = prompts.world_building_question(round_index, qa)
    question = client.chat_text(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    return question.strip().strip('"').strip("'")


async def generate_world_question_async(client: LLMProvider, qa: list, round_index: int) -> str:
    system, user = prompts.world_building_question(round_index, qa)
    question = await client.chat_text_async(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    return question.strip().strip('"').strip("'")


def summarize_world(client: LLMProvider, qa: list) -> World:
    system = prompts.summarize_world(qa)
    user = "问答内容：" + str(qa)
    summary = client.chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    if not summary:
        return World()
    return World(
        time=summary.get("time", ""),
        place=summary.get("place", ""),
        people=list(summary.get("people", [])),
        rules=summary.get("rules", ""),
        tone=summary.get("tone", ""),
        notes=list(summary.get("notes", [])),
    )


async def summarize_world_async(client: LLMProvider, qa: list) -> World:
    system = prompts.summarize_world(qa)
    user = "问答内容：" + str(qa)
    summary = await client.chat_json_async(
        [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    if not summary:
        return World()
    return World(
        time=summary.get("time", ""),
        place=summary.get("place", ""),
        people=list(summary.get("people", [])),
        rules=summary.get("rules", ""),
        tone=summary.get("tone", ""),
        notes=list(summary.get("notes", [])),
    )


def build_world(client: LLMProvider) -> tuple[World, list]:
    qa: list = []
    console.print("\n[bold cyan]进入世界观构建（5 轮问答）[/bold cyan]")
    for i in range(1, 6):
        question = generate_world_question(client, qa, i)
        console.print(f"\n[bold yellow][世界观问答 {i}/5][/bold yellow] {question}")
        answer = console.input("[dim]> [/dim]").strip()
        qa.append({"question": question, "answer": answer})

    world = summarize_world(client, qa)
    return world, qa


class WorldBuilder:
    """Event-driven world builder for Web UI."""

    def __init__(self, client: LLMProvider) -> None:
        self.client = client
        self.qa: list[dict[str, str]] = []
        self.current_question: str = ""
        self.step = 0  # 0..5, step means how many Q&A pairs completed

    def next_question_sync(self) -> str:
        self.step += 1
        question = generate_world_question(self.client, self.qa, self.step)
        self.current_question = question
        return question

    async def next_question_async(self) -> str:
        self.step += 1
        question = await generate_world_question_async(self.client, self.qa, self.step)
        self.current_question = question
        return question

    def submit_answer(self, answer: str) -> None:
        if not self.current_question:
            raise RuntimeError("No active question")
        self.qa.append({"question": self.current_question, "answer": answer})
        self.current_question = ""

    def is_complete(self) -> bool:
        return self.step >= 5 and not self.current_question

    def summarize_sync(self) -> World:
        return summarize_world(self.client, self.qa)

    async def summarize_async(self) -> World:
        return await summarize_world_async(self.client, self.qa)
