"""Tests for memory and token-aware context management."""

from unittest.mock import MagicMock

from lonely_world.game.memory import (
    COMPRESSION_TURN_THRESHOLD,
    estimate_message_tokens,
    estimate_tokens,
    maybe_compress_memory,
    select_conversation_context,
)
from lonely_world.models import Character, CharacterState, ConversationRecord, World


class TestTokenEstimation:
    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 0

    def test_estimate_tokens_chinese(self):
        text = "这是一个测试"
        assert estimate_tokens(text) == int(len(text) * 1.5)

    def test_estimate_message_tokens(self):
        msg = {"role": "user", "content": "hello"}
        assert estimate_message_tokens(msg) == estimate_tokens("hello") + 4


class TestSelectConversationContext:
    def test_empty_conversation(self):
        result = select_conversation_context([], "hi")
        assert result == []

    def test_all_messages_fit(self):
        records = [
            ConversationRecord(role="user", content="a", ts="1"),
            ConversationRecord(role="assistant", content="b", ts="2"),
        ]
        result = select_conversation_context(records, "hi", budget=1000)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_budget_limits_messages(self):
        # Create a long message that alone exceeds budget
        long_text = "x" * 1000
        records = [
            ConversationRecord(role="user", content=long_text, ts="1"),
            ConversationRecord(role="assistant", content="short", ts="2"),
        ]
        # budget allows only the most recent exchange
        result = select_conversation_context(records, "hi", budget=50)
        # Only the assistant "short" + user_input overhead might still allow it
        # Since budget is tiny, it may return 0 or 1 depending on user_input cost
        assert len(result) <= 1

    def test_order_preserved(self):
        records = [
            ConversationRecord(role="user", content="first", ts="1"),
            ConversationRecord(role="assistant", content="second", ts="2"),
            ConversationRecord(role="user", content="third", ts="3"),
        ]
        result = select_conversation_context(records, "hi", budget=1000)
        assert result[0]["content"] == "first"
        assert result[-1]["content"] == "third"


class TestMaybeCompressMemory:
    def test_no_compression_when_under_threshold(self):
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        client = MagicMock()
        assert maybe_compress_memory(char, client, "gpt-4") is False

    def test_compression_when_over_threshold(self):
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        for i in range(COMPRESSION_TURN_THRESHOLD + 2):
            char.conversation.append(ConversationRecord(role="user", content=f"u{i}", ts="t"))
            char.conversation.append(ConversationRecord(role="assistant", content=f"a{i}", ts="t"))

        client = MagicMock()
        client.chat_text.return_value = " summarized memory "
        assert maybe_compress_memory(char, client, "gpt-4") is True
        assert "summarized memory" in char.memory_summary
        # Half of the conversation should be removed
        assert len(char.conversation) < COMPRESSION_TURN_THRESHOLD * 2
        client.chat_text.assert_called_once()

    def test_compression_failed_gracefully(self):
        char = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        for i in range(COMPRESSION_TURN_THRESHOLD + 2):
            char.conversation.append(ConversationRecord(role="user", content=f"u{i}", ts="t"))
            char.conversation.append(ConversationRecord(role="assistant", content=f"a{i}", ts="t"))

        client = MagicMock()
        client.chat_text.side_effect = Exception("API error")
        assert maybe_compress_memory(char, client, "gpt-4") is False
