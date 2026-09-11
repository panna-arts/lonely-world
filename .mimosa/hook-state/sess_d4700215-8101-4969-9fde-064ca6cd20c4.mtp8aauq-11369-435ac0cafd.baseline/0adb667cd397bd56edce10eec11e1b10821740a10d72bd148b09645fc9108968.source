"""Tests for data models."""

from lonely_world.models import (
    Character,
    CharacterState,
    ConversationRecord,
    GameConfig,
    World,
)


class TestWorld:
    def test_default_creation(self):
        w = World()
        assert w.time == ""
        assert w.place == ""
        assert w.people == []
        assert w.rules == ""

    def test_round_trip(self):
        w = World(time="古代", place="长安", people=["李白"])
        d = w.to_dict()
        w2 = World.from_dict(d)
        assert w2.time == "古代"
        assert w2.place == "长安"
        assert w2.people == ["李白"]


class TestCharacterState:
    def test_round_trip(self):
        s = CharacterState(items=["剑"], skills=["武艺"])
        d = s.to_dict()
        s2 = CharacterState.from_dict(d)
        assert s2.items == ["剑"]
        assert s2.skills == ["武艺"]


class TestCharacter:
    def test_round_trip(self):
        c = Character(
            name="测试",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
            world=World(time="古代", place="长安"),
            state=CharacterState(items=["剑"]),
            memory_summary="测试记忆",
        )
        c.conversation.append(
            ConversationRecord(role="user", content="你好", ts="2025-01-01T00:00:01")
        )
        d = c.to_dict()
        c2 = Character.from_dict(d)
        assert c2.name == "测试"
        assert c2.world.time == "古代"
        assert c2.state.items == ["剑"]
        assert c2.memory_summary == "测试记忆"
        assert len(c2.conversation) == 1
        assert c2.conversation[0].role == "user"


class TestGameConfig:
    def test_defaults(self):
        cfg = GameConfig()
        assert cfg.provider == "openai"
        assert cfg.enable_story_append is False

    def test_round_trip(self):
        cfg = GameConfig(provider="anthropic", model="claude-3", enable_story_append=True)
        d = cfg.to_dict()
        cfg2 = GameConfig.from_dict(d)
        assert cfg2.provider == "anthropic"
        assert cfg2.model == "claude-3"
        assert cfg2.enable_story_append is True


class TestSchemaVersion:
    def test_character_has_schema_version(self):
        c = Character(
            name="测试", created_at="", updated_at="", world=World(), state=CharacterState()
        )
        d = c.to_dict()
        assert d.get("schema_version") == "2"
        c2 = Character.from_dict(d)
        assert c2.schema_version == "2"

    def test_v1_migration_adds_notes(self):
        old_data = {
            "name": "老角色",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "world": {"time": "古代", "place": "长安", "people": ["李白"]},
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
        c = Character.from_dict(old_data)
        assert c.schema_version == "2"
        assert c.world.notes == []
        assert "schema_version" in c.to_dict()
