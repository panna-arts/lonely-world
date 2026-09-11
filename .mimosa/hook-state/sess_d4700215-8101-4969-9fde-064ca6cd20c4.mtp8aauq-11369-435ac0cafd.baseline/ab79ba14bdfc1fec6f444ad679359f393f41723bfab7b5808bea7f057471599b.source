"""Tests for OpenAI provider edge cases."""

from lonely_world.llm.openai_provider import _parse_json


class TestParseJson:
    def test_valid_json(self):
        assert _parse_json('{"key": "value"}') == {"key": "value"}

    def test_json_with_surrounding_text(self):
        assert _parse_json('prefix {"key": "value"} suffix') == {"key": "value"}

    def test_invalid_json(self):
        assert _parse_json("not json") is None

    def test_nested_braces_invalid(self):
        assert _parse_json("some text {broken json") is None
