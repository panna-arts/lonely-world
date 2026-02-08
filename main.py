import json
import os
import sys
from datetime import datetime
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHAR_DIR = DATA_DIR / "characters"
CONFIG_FILE = DATA_DIR / "config.json"
DEFAULT_MODEL = "gpt-5-mini"


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHAR_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config() -> Dict[str, Any]:
    ensure_dirs()
    return read_json(CONFIG_FILE, {})


def save_config(cfg: Dict[str, Any]) -> None:
    write_json(CONFIG_FILE, cfg)


def ensure_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    env_key = os.getenv("OPENAI_API_KEY") or os.getenv("LONELY_WORLD_API_KEY")
    env_base = os.getenv("OPENAI_BASE_URL") or os.getenv("LONELY_WORLD_BASE_URL")
    env_model = os.getenv("LONELY_WORLD_MODEL")
    changed = False

    if env_key:
        if cfg.get("api_key") != env_key:
            cfg["api_key"] = env_key
            changed = True
    elif not cfg.get("api_key"):
        key = getpass("请输入大模型 API Key: ").strip()
        if key:
            cfg["api_key"] = key
            changed = True
        else:
            print("未配置 API Key，无法继续。")
            sys.exit(1)

    if env_base:
        if cfg.get("base_url") != env_base:
            cfg["base_url"] = env_base
            changed = True
    elif not cfg.get("base_url"):
        while True:
            base_url = input("请输入 API Base URL: ").strip()
            if base_url:
                cfg["base_url"] = base_url
                changed = True
                break
            print("Base URL 不能为空。")

    if env_model:
        if cfg.get("model") != env_model:
            cfg["model"] = env_model
            changed = True
    elif not cfg.get("model"):
        while True:
            model_input = input(f"请输入模型名称 (例如 {DEFAULT_MODEL}): ").strip()
            if model_input:
                cfg["model"] = model_input
                changed = True
                break
            print("模型名称不能为空。")

    if changed:
        save_config(cfg)
    return cfg


def get_client(cfg: Dict[str, Any]) -> OpenAI:
    key = cfg["api_key"]
    base_url = cfg.get("base_url") or os.getenv("OPENAI_BASE_URL") or os.getenv("LONELY_WORLD_BASE_URL")
    if base_url:
        return OpenAI(api_key=key, base_url=base_url)
    return OpenAI(api_key=key)


def safe_name(name: str) -> str:
    cleaned = name.strip()
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        cleaned = cleaned.replace(ch, "_")
    return cleaned or "无名"


def legacy_character_path(name: str) -> Path:
    return CHAR_DIR / f"{safe_name(name)}.json"


def character_dir(name: str) -> Path:
    return CHAR_DIR / safe_name(name)


def character_json_path(name: str) -> Path:
    return character_dir(name) / "character.json"


def character_story_path(name: str) -> Path:
    return character_dir(name) / "story.md"


def prepare_character_storage(name: str) -> Dict[str, Path]:
    legacy_path = legacy_character_path(name)
    char_dir = character_dir(name)
    json_path = character_json_path(name)
    story_path = character_story_path(name)

    if legacy_path.exists():
        char_dir.mkdir(parents=True, exist_ok=True)
        if json_path.exists():
            backup = char_dir / f"legacy_{now_ts().replace(':', '-')}.json"
            legacy_path.rename(backup)
        else:
            legacy_path.rename(json_path)

    return {"dir": char_dir, "json": json_path, "story": story_path}


def create_character(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "created_at": now_ts(),
        "updated_at": now_ts(),
        "world": {
            "time": "",
            "place": "",
            "people": [],
            "rules": "",
            "tone": "",
            "notes": [],
        },
        "state": {
            "items": [],
            "skills": [],
            "traits": [],
            "personality": "",
            "status": "",
            "relationships": {},
            "notes": [],
        },
        "memory_summary": "",
        "world_qa": [],
        "conversation": [],
    }


def show_recent_conversation(character: Dict[str, Any], limit_pairs: int = 6) -> None:
    records = [m for m in character.get("conversation", []) if m.get("role") in ("user", "assistant")]
    if not records:
        return
    print("\n上次对话回顾：")
    tail = records[-limit_pairs * 2 :]
    for msg in tail:
        role = "你" if msg.get("role") == "user" else character.get("name", "NPC")
        print(f"{role}：{msg.get('content', '')}")
    print("")


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


def generate_story_append(
    client: OpenAI,
    model: str,
    character: Dict[str, Any],
    user_input: str,
    assistant_reply: str,
    story_path: Path,
) -> str:
    story_tail = read_story_tail(story_path, 1200)
    system = (
        "你是文学作家，将文字冒险的互动续写成高质量中文文学作品。"
        "要求语言精炼、有画面感，避免口水与赘述。"
        "每次续写 1-3 段，总字数约 200-400 字。"
        "只输出正文，不要标题或额外说明。"
    )
    payload = {
        "character": character.get("name"),
        "world": character.get("world"),
        "state": character.get("state"),
        "memory_summary": character.get("memory_summary"),
        "world_qa": character.get("world_qa"),
        "last_story": story_tail,
        "latest_input": user_input,
        "latest_reply": assistant_reply,
    }
    user = "背景与上下文：" + json.dumps(payload, ensure_ascii=False)
    story = chat_text(client, model, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    return story.strip()


def chat_text(client: OpenAI, model: str, messages: List[Dict[str, str]]) -> str:
    completion = client.chat.completions.create(model=model, messages=messages)
    return completion.choices[0].message.content or ""


def chat_json(client: OpenAI, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content or "{}"
    parsed = parse_json(content)
    return parsed or {}


def parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def generate_world_question(
    client: OpenAI, model: str, qa: List[Dict[str, str]], round_index: int
) -> str:
    system = (
        "你是世界观构建引导者。通过 5 轮问答引导玩家共同建立世界观，"
        "必须覆盖时间、地点、人物与社会风貌。现在是第 "
        f"{round_index}/5 轮。只输出一个简短问题，不要附加说明。"
    )
    user = (
        "已收集问答："
        + json.dumps(qa, ensure_ascii=False)
        + "。请给出本轮问题。"
    )
    question = chat_text(client, model, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    return question.strip().strip("“”\" ")


def summarize_world(client: OpenAI, model: str, qa: List[Dict[str, str]]) -> Dict[str, Any]:
    system = (
        "根据 5 轮问答总结世界观。输出严格 JSON："
        "{time, place, people, rules, tone, notes}。"
        "其中 people 为字符串数组，notes 为字符串数组。"
        "只输出 JSON，不要附加说明。"
    )
    user = "问答内容：" + json.dumps(qa, ensure_ascii=False)
    summary = chat_json(client, model, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    if not summary:
        return {
            "time": "",
            "place": "",
            "people": [],
            "rules": "",
            "tone": "",
            "notes": [],
        }
    summary.setdefault("people", [])
    summary.setdefault("notes", [])
    return summary


def build_world(client: OpenAI, model: str) -> Dict[str, Any]:
    qa: List[Dict[str, str]] = []
    print("\n进入世界观构建（5 轮问答）")
    for i in range(1, 6):
        question = generate_world_question(client, model, qa, i)
        print(f"\n[世界观问答 {i}/5] {question}")
        answer = input("> ").strip()
        qa.append({"question": question, "answer": answer})

    world = summarize_world(client, model, qa)
    world["qa"] = qa
    return world


def build_game_messages(character: Dict[str, Any], user_input: str) -> List[Dict[str, str]]:
    system = (
        "你是文字冒险游戏的叙事智能体。没有既定故事线，"
        "所有故事都由玩家输入与互动推进。必须尊重并延续世界观和角色长期状态。"
        "输出严格 JSON："
        "{reply, character_state, world_state, memory_summary}。"
        "character_state 与 world_state 必须为完整对象（不只是变更）。"
        "reply 用中文，简洁、有画面感，避免替玩家做决定。"
        "若没有变化，也必须原样返回当前状态。"
        "\n\n当前角色状态："
        + json.dumps(character["state"], ensure_ascii=False)
        + "\n当前世界观："
        + json.dumps(character["world"], ensure_ascii=False)
        + "\n长期记忆摘要："
        + (character.get("memory_summary") or "")
    )

    recent = [m for m in character.get("conversation", []) if m.get("role") in ("user", "assistant")][-12:]
    messages = [{"role": "system", "content": system}]
    messages.extend({"role": m["role"], "content": m["content"]} for m in recent)
    messages.append({"role": "user", "content": user_input})
    return messages


def play_loop(
    client: OpenAI,
    model: str,
    character: Dict[str, Any],
    json_path: Path,
    story_path: Path,
) -> None:
    print("\n进入游戏。输入 退出 / quit / exit 可结束并保存。\n")
    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input.lower() in {"退出", "quit", "exit"}:
            character["updated_at"] = now_ts()
            write_json(json_path, character)
            print("已保存，期待下次继续。")
            return

        try:
            messages = build_game_messages(character, user_input)
            result = chat_json(client, model, messages)
        except Exception as exc:  # noqa: BLE001
            print(f"调用失败：{exc}")
            continue

        reply = result.get("reply") if isinstance(result, dict) else None
        if not reply:
            reply = "（智能体没有返回有效内容，请重试。）"

        character["conversation"].append({"role": "user", "content": user_input, "ts": now_ts()})
        character["conversation"].append({"role": "assistant", "content": reply, "ts": now_ts()})

        if isinstance(result, dict):
            character["state"] = result.get("character_state", character["state"])
            character["world"] = result.get("world_state", character["world"])
            if result.get("memory_summary"):
                character["memory_summary"] = result["memory_summary"]

        try:
            story_append = generate_story_append(client, model, character, user_input, reply, story_path)
            if story_append:
                append_story(story_path, character.get("name", "无名"), story_append)
        except Exception as exc:  # noqa: BLE001
            print(f"故事续写失败：{exc}")

        character["updated_at"] = now_ts()
        write_json(json_path, character)
        print(f"\n{character['name']}：{reply}\n")


def main() -> None:
    ensure_dirs()
    cfg = load_config()
    cfg = ensure_config(cfg)
    client = get_client(cfg)
    model = cfg.get("model", DEFAULT_MODEL)

    name = input("请输入角色名称：").strip()
    if not name:
        print("角色名称不能为空。")
        return

    storage = prepare_character_storage(name)
    json_path = storage["json"]
    story_path = storage["story"]

    if json_path.exists():
        character = read_json(json_path, create_character(name))
        print(f"已载入角色：{character.get('name', name)}")
        show_recent_conversation(character)
    else:
        character = create_character(name)
        world = build_world(client, model)
        character["world"] = {
            "time": world.get("time", ""),
            "place": world.get("place", ""),
            "people": world.get("people", []),
            "rules": world.get("rules", ""),
            "tone": world.get("tone", ""),
            "notes": world.get("notes", []),
        }
        character["world_qa"] = world.get("qa", [])
        character["memory_summary"] = (
            f"世界观：时间={character['world']['time']}；地点={character['world']['place']}；"
            f"人物={','.join(character['world']['people'])}。"
        )
        write_json(json_path, character)
        print("\n世界观已建立，角色已创建并保存。")

    play_loop(client, model, character, json_path, story_path)


if __name__ == "__main__":
    main()
