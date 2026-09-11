"""Data models for lonely-world."""

from dataclasses import dataclass, field


@dataclass
class World:
    time: str = ""
    place: str = ""
    people: list[str] = field(default_factory=list)
    rules: str = ""
    tone: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "place": self.place,
            "people": list(self.people),
            "rules": self.rules,
            "tone": self.tone,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "World":
        return cls(
            time=data.get("time", ""),
            place=data.get("place", ""),
            people=list(data.get("people", [])),
            rules=data.get("rules", ""),
            tone=data.get("tone", ""),
            notes=list(data.get("notes", [])),
        )


@dataclass
class CharacterState:
    items: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    personality: str = ""
    status: str = ""
    relationships: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "items": list(self.items),
            "skills": list(self.skills),
            "traits": list(self.traits),
            "personality": self.personality,
            "status": self.status,
            "relationships": dict(self.relationships),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterState":
        return cls(
            items=list(data.get("items", [])),
            skills=list(data.get("skills", [])),
            traits=list(data.get("traits", [])),
            personality=data.get("personality", ""),
            status=data.get("status", ""),
            relationships=dict(data.get("relationships", {})),
            notes=list(data.get("notes", [])),
        )


@dataclass
class ConversationRecord:
    role: str
    content: str
    ts: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "ts": self.ts}


_CHARACTER_SCHEMA_VERSION = "2"


@dataclass
class Character:
    name: str
    created_at: str
    updated_at: str
    world: World
    state: CharacterState
    memory_summary: str = ""
    world_qa: list[dict[str, str]] = field(default_factory=list)
    conversation: list[ConversationRecord] = field(default_factory=list)
    schema_version: str = _CHARACTER_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "world": self.world.to_dict(),
            "state": self.state.to_dict(),
            "memory_summary": self.memory_summary,
            "world_qa": list(self.world_qa),
            "conversation": [m.to_dict() for m in self.conversation],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        version = data.get("schema_version", "1")
        if version == "1":
            # Migrate from v1: ensure world has all new fields with defaults
            world_data = data.get("world", {})
            world_data.setdefault("notes", [])
            data["world"] = world_data
            data["schema_version"] = _CHARACTER_SCHEMA_VERSION
        return cls(
            schema_version=data.get("schema_version", _CHARACTER_SCHEMA_VERSION),
            name=data.get("name", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            world=World.from_dict(data.get("world", {})),
            state=CharacterState.from_dict(data.get("state", {})),
            memory_summary=data.get("memory_summary", ""),
            world_qa=list(data.get("world_qa", [])),
            conversation=[
                ConversationRecord(**m) for m in data.get("conversation", []) if isinstance(m, dict)
            ],
        )


@dataclass
class GameConfig:
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    provider: str = "openai"
    enable_story_append: bool = False

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "provider": self.provider,
            "enable_story_append": self.enable_story_append,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameConfig":
        return cls(
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            model=data.get("model", ""),
            provider=data.get("provider", "openai"),
            enable_story_append=data.get("enable_story_append", False),
        )
