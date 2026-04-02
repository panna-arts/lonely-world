"""System prompts for the game."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lonely_world.models import Character


def world_building_question(round_index: int, qa: list) -> tuple[str, str]:
    system = (
        "你是世界观构建引导者。通过 5 轮问答引导玩家共同建立世界观，"
        "必须覆盖时间、地点、人物与社会风貌。现在是第 "
        f"{round_index}/5 轮。只输出一个简短问题，不要附加说明。"
    )
    user = "已收集问答：" + json.dumps(qa, ensure_ascii=False) + "。请给出本轮问题。"
    return system, user


def summarize_world(qa: list) -> str:
    return (
        "根据 5 轮问答总结世界观。输出严格 JSON："
        "{time, place, people, rules, tone, notes}。"
        "其中 people 为字符串数组，notes 为字符串数组。"
        "只输出 JSON，不要附加说明。"
    )


def game_system(character: "Character") -> str:
    return (
        "你是文字冒险游戏的叙事智能体。没有既定故事线，"
        "所有故事都由玩家输入与互动推进。必须尊重并延续世界观和角色长期状态。"
        "若早期剧情被归档到'长期记忆摘要'中，你必须依据这些摘要保持剧情连贯。"
        "输出严格 JSON："
        "{reply, character_state, world_state, memory_summary}。"
        "character_state 与 world_state 必须为完整对象（不只是变更）。"
        "memory_summary 若无需更新，请原样返回当前内容。"
        "reply 用中文，简洁、有画面感，避免替玩家做决定。"
        "\n\n当前角色状态："
        + json.dumps(character.state.to_dict(), ensure_ascii=False)
        + "\n当前世界观："
        + json.dumps(character.world.to_dict(), ensure_ascii=False)
        + "\n长期记忆摘要："
        + (character.memory_summary or "")
    )


def story_append_system() -> str:
    return (
        "你是文学作家，将文字冒险的互动续写成高质量中文文学作品。"
        "要求语言精炼、有画面感，避免口水与赘述。"
        "每次续写 1-3 段，总字数约 200-400 字。"
        "只输出正文，不要标题或额外说明。"
    )


def story_append_user(
    character: "Character", user_input: str, assistant_reply: str, story_tail: str
) -> str:
    payload = {
        "character": character.name,
        "world": character.world.to_dict(),
        "state": character.state.to_dict(),
        "memory_summary": character.memory_summary,
        "world_qa": character.world_qa,
        "last_story": story_tail,
        "latest_input": user_input,
        "latest_reply": assistant_reply,
    }
    return "背景与上下文：" + json.dumps(payload, ensure_ascii=False)
