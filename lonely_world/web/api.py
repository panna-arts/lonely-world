"""API routes for the lonely-world Web UI."""

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from starlette.requests import Request as StarletteRequest

from lonely_world.game.engine import GameEngine
from lonely_world.game.world import WorldBuilder
from lonely_world.models import Character, CharacterState
from lonely_world.storage import now_ts
from lonely_world.web.events import format_sse
from lonely_world.web.session import WebConfigError, store
from lonely_world.web.storage import SessionStorage

router = APIRouter()


def _ensure_session(request: Request) -> str:
    return store.ensure_session_id(request)


def _session_storage(session_id: str) -> SessionStorage:
    return SessionStorage(session_id)


@router.get("/api/config")
async def get_config(request: StarletteRequest) -> dict:
    try:
        cfg = store.config
    except WebConfigError as exc:
        return {"ok": False, "error": str(exc)}
    _ensure_session(request)
    return {
        "ok": True,
        "provider": cfg.provider,
        "model": cfg.model,
        "base_url": cfg.base_url,
        "enable_story_append": cfg.enable_story_append,
    }


@router.get("/api/characters")
async def list_characters(request: StarletteRequest) -> dict:
    session_id = _ensure_session(request)
    storage = _session_storage(session_id)
    return {"characters": storage.list_characters()}


@router.post("/api/create")
async def create_character(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    name = payload.get("name", "").strip()
    if not name:
        return {"ok": False, "error": "角色名称不能为空"}

    storage = _session_storage(session_id)
    existing = storage.load_character(name)
    if existing is not None:
        return {"ok": False, "error": "角色已存在，请直接加载"}

    builder = WorldBuilder(store.provider)
    store.set_builder(session_id, builder)
    store.set_character_name(session_id, name)
    question = await builder.next_question_async()
    return {"ok": True, "step": builder.step, "question": question}


@router.post("/api/world/answer")
async def world_answer(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    builder = store.get_builder(session_id)
    if builder is None:
        return {"ok": False, "error": "尚未开始世界观构建"}

    answer = payload.get("answer", "").strip()
    if not answer:
        return {"ok": False, "error": "回答不能为空"}

    builder.submit_answer(answer)

    if builder.is_complete():
        world = await builder.summarize_async()
        name = store.get_character_name(session_id) or "无名"
        character = Character(
            name=name,
            created_at=now_ts(),
            updated_at=now_ts(),
            world=world,
            state=CharacterState(),
        )
        character.world_qa = [
            {"question": q["question"], "answer": q["answer"]} for q in builder.qa
        ]
        character.memory_summary = (
            f"世界观：时间={character.world.time}；"
            f"地点={character.world.place}；"
            f"人物={','.join(character.world.people)}。"
        )
        storage = _session_storage(session_id)
        paths = storage.prepare_character_storage(name)
        storage.save_character(character, paths["json"])
        store.clear_builder(session_id)
        return {
            "ok": True,
            "complete": True,
            "character": {
                "name": character.name,
                "world": character.world.to_dict(),
                "memory_summary": character.memory_summary,
            },
        }

    question = await builder.next_question_async()
    return {
        "ok": True,
        "complete": False,
        "step": builder.step,
        "question": question,
    }


@router.post("/api/load")
async def load_character_route(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    name = payload.get("name", "").strip()
    if not name:
        return {"ok": False, "error": "角色名称不能为空"}

    storage = _session_storage(session_id)
    character = storage.load_character(name)
    if character is None:
        return {"ok": False, "error": "角色不存在"}

    paths = storage.prepare_character_storage(name)
    enable_story_append = store.get_story_append(session_id)
    engine = GameEngine(
        client=store.provider,
        character=character,
        json_path=paths["json"],
        story_path=paths["story"],
        export_story_dir=paths["export_story_dir"],
        export_character_dir=paths["export_character_dir"],
        enable_story_append=enable_story_append,
    )
    store.set_engine(session_id, engine)
    store.set_character_name(session_id, name)

    recent = [
        {"role": m.role, "content": m.content}
        for m in character.conversation
        if m.role in ("user", "assistant")
    ]
    return {
        "ok": True,
        "character": {
            "name": character.name,
            "world": character.world.to_dict(),
            "state": character.state.to_dict(),
            "memory_summary": character.memory_summary,
        },
        "conversation": recent,
    }


@router.post("/api/chat")
async def chat(request: StarletteRequest, payload: dict) -> StreamingResponse:
    session_id = _ensure_session(request)
    engine = store.get_engine(session_id)
    message = payload.get("message", "").strip()

    if not message:
        return StreamingResponse(
            iter([format_sse({"type": "error", "message": "消息不能为空"})]),
            media_type="text/event-stream",
        )

    if engine is None:
        return StreamingResponse(
            iter(
                [
                    format_sse(
                        {
                            "type": "error",
                            "message": "没有进行中的游戏，请先选择或创建角色",
                        }
                    )
                ]
            ),
            media_type="text/event-stream",
        )

    async def event_generator():
        engine.snapshot()
        compressed = engine.maybe_compress_memory()
        if compressed:
            yield format_sse({"type": "system", "message": "已自动归档早期对话到长期记忆"})
        async for event in engine.process_turn_stream(message):
            yield format_sse(event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/undo")
async def undo(request: StarletteRequest) -> dict:
    session_id = _ensure_session(request)
    engine = store.get_engine(session_id)
    if engine is None:
        return {"ok": False, "error": "没有进行中的游戏"}
    success = engine.undo()
    return {"ok": success}


@router.get("/api/story")
async def get_story(request: StarletteRequest) -> PlainTextResponse:
    session_id = _ensure_session(request)
    engine = store.get_engine(session_id)
    if engine is None:
        return PlainTextResponse("没有进行中的游戏", status_code=400)
    tail = engine.read_story_tail(1200)
    return PlainTextResponse(tail or "暂无故事内容")


@router.post("/api/export/story")
async def export_story_route(request: StarletteRequest) -> dict:
    session_id = _ensure_session(request)
    engine = store.get_engine(session_id)
    if engine is None:
        return {"ok": False, "error": "没有进行中的游戏"}
    path = engine.export_story_file()
    return {"ok": True, "path": str(path) if path else None}


@router.post("/api/export/role")
async def export_role_route(request: StarletteRequest) -> dict:
    session_id = _ensure_session(request)
    engine = store.get_engine(session_id)
    if engine is None:
        return {"ok": False, "error": "没有进行中的游戏"}
    path = engine.export_role_file()
    return {"ok": True, "path": str(path)}


@router.post("/api/toggle-story-append")
async def toggle_story_append(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    enabled = bool(payload.get("enabled", False))
    store.set_story_append(session_id, enabled)
    engine = store.get_engine(session_id)
    if engine is not None:
        engine.enable_story_append = enabled
    return {"ok": True, "enabled": enabled}


@router.post("/api/characters/delete")
async def delete_character_route(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    name = payload.get("name", "").strip()
    if not name:
        return {"ok": False, "error": "角色名称不能为空"}
    storage = _session_storage(session_id)
    removed = storage.delete_character(name)
    return {"ok": removed}


@router.post("/api/characters/rename")
async def rename_character_route(request: StarletteRequest, payload: dict) -> dict:
    session_id = _ensure_session(request)
    old_name = payload.get("old_name", "").strip()
    new_name = payload.get("new_name", "").strip()
    if not old_name or not new_name:
        return {"ok": False, "error": "名称不能为空"}
    storage = _session_storage(session_id)
    ok = storage.rename_character(old_name, new_name)
    return {"ok": ok}
