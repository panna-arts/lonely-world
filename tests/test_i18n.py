"""Tests for i18n fallback and edge cases."""

import pytest

from lonely_world import i18n
from lonely_world.web.api import MAX_INPUT_LENGTH


def test_i18n_unknown_key_returns_key():
    """Unknown keys should return the key itself as fallback."""
    assert i18n._("unknown.module.key") == "unknown.module.key"


def test_i18n_partial_key_traversal():
    """If a path partially matches, the non-matching part is used as-is."""
    # e.g. "api.char_name" when "api.char_name_empty" exists returns key
    result = i18n._("api.char_name_empty")
    assert result == "角色名称不能为空"


def test_world_builder_en_prompts():
    """English locale world builder prompts work."""
    sys_en, user_en = i18n.world_builder_prompts(3, [{"q": "a"}], locale="en")
    assert "3/5" in sys_en
    assert "Collected Q&A" in user_en


def test_world_builder_zh_prompts():
    """Chinese locale world builder prompts work."""
    sys_zh, user_zh = i18n.world_builder_prompts(3, [{"q": "a"}], locale="zh")
    assert "3/5" in sys_zh
    assert "已收集问答" in user_zh


def test_locale_caching():
    """Locale dicts are cached after first load."""
    i18n._cached.clear()
    assert "zh" not in i18n._cached
    i18n._("cli.help_lines", locale="zh")
    assert "zh" in i18n._cached


def test_format_args():
    """Format arguments work in i18n strings."""
    text = i18n._("api.input_too_long", limit=MAX_INPUT_LENGTH)
    assert str(MAX_INPUT_LENGTH) in text


def test_nested_list_indexing():
    """List values can be joined."""
    text = i18n._("cli.help_lines")
    assert isinstance(text, str)
    assert len(text) > 0