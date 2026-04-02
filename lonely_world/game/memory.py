"""Memory compression and token-aware context management."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lonely_world.llm.base import LLMProvider
    from lonely_world.models import Character, ConversationRecord

logger = logging.getLogger(__name__)

# Budget for conversation history in tokens (reserve room for system prompt + response)
DEFAULT_HISTORY_TOKEN_BUDGET = 6000
# Trigger automatic memory compression after this many conversation turns
COMPRESSION_TURN_THRESHOLD = 30
# Tokens per Chinese char ≈ 1.0~1.5; English word ≈ 1.3; use conservative heuristic
TOKEN_ESTIMATE_FACTOR = 1.5


def estimate_tokens(text: str) -> int:
    """Roughly estimate token count for budgeting purposes."""
    if not text:
        return 0
    # Heuristic: mixed CJK and ASCII text averages around 1.5 tokens per char/word boundary
    return max(1, int(len(text) * TOKEN_ESTIMATE_FACTOR))


def estimate_message_tokens(msg: dict) -> int:
    """Estimate tokens for a single message dict."""
    content = msg.get("content", "")
    # Add overhead for role and formatting
    return estimate_tokens(content) + 4


def select_conversation_context(
    conversation: list["ConversationRecord"],
    user_input: str,
    budget: int = DEFAULT_HISTORY_TOKEN_BUDGET,
) -> list[dict]:
    """Select recent conversation messages within token budget.

    Always keeps the very latest exchanges and drops older ones if needed.
    """
    records = [m for m in conversation if m.role in ("user", "assistant")]
    if not records:
        return []

    # Work backwards from the most recent message
    selected = []
    current_budget = budget - estimate_message_tokens({"role": "user", "content": user_input})

    for record in reversed(records):
        msg = {"role": record.role, "content": record.content}
        cost = estimate_message_tokens(msg)
        if cost <= current_budget:
            selected.append(msg)
            current_budget -= cost
        else:
            break

    selected.reverse()
    return selected


def maybe_compress_memory(character: "Character", client: "LLMProvider", model: str) -> bool:
    """Compress early conversation history into memory_summary if threshold is met.

    Returns True if compression was performed.
    """
    records = [m for m in character.conversation if m.role in ("user", "assistant")]
    if len(records) < COMPRESSION_TURN_THRESHOLD:
        return False

    # Take the oldest half of conversations to compress
    half = len(records) // 2
    to_compress = records[:half]
    preserved = records[half:]

    summary_text = _summarize_conversations(client, model, to_compress)
    if summary_text:
        if character.memory_summary:
            character.memory_summary += "\n\n[归档记忆]\n" + summary_text
        else:
            character.memory_summary = "[归档记忆]\n" + summary_text
        character.conversation = list(preserved)
        logger.info("Memory compressed: %d turns summarized", half)
        return True
    return False


def _summarize_conversations(
    client: "LLMProvider", model: str, records: list["ConversationRecord"]
) -> str:
    """Ask LLM to summarize a slice of conversation into a short paragraph."""
    lines = []
    for r in records:
        speaker = "玩家" if r.role == "user" else "叙事"
        lines.append(f"{speaker}：{r.content}")
    transcript = "\n".join(lines)

    system = (
        "你是记忆整理助手。请将以下文字冒险游戏的对话记录"
        "总结为一段 100-200 字的叙事摘要，保留关键事件、人物关系和地点变化。"
        "只输出摘要正文，不要标题和说明。"
    )
    user = f"对话记录：\n{transcript}\n\n请总结。"
    try:
        summary = client.chat_text(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        return summary.strip()
    except Exception as exc:
        logger.warning("Memory compression failed: %s", exc)
        return ""
