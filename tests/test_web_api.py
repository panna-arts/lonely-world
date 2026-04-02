"""Tests for Web UI API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from lonely_world.models import GameConfig, World
from lonely_world.web import main, session
from lonely_world.web.session import store

# Create a mock provider
_mock_provider = MagicMock()
_mock_provider.chat_text_async = AsyncMock(return_value="测试问题")
_mock_provider.chat_json_async = AsyncMock(return_value={"reply": "测试回复"})

# Completely bypass real config loading so no env vars or interactive prompts are needed
session.SessionStore.load_server_config = lambda self: (
    setattr(
        self,
        "_config",
        GameConfig(
            api_key="test", base_url="http://localhost/v1", model="gpt-test", provider="openai"
        ),
    )
    or setattr(self, "_provider", _mock_provider)
    or self._config
)

# Ensure config is loaded before creating TestClient
store.load_server_config()

client = TestClient(main.app)


class TestWebConfig:
    def test_get_config(self):
        res = client.get("/api/config")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-test"


class TestCharacterFlow:
    def test_list_characters_empty(self):
        res = client.get("/api/characters")
        assert res.status_code == 200
        assert res.json()["characters"] == []

    def test_create_and_world_build(self):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async", new_callable=AsyncMock
        ) as mock_summarize:
            mock_summarize.return_value = World(time="古代", place="长安", people=["李白"])
            # Start creation
            res = client.post("/api/create", json={"name": "李逍遥"})
            assert res.status_code == 200
            data = res.json()
            assert data["ok"] is True
            assert data["step"] == 1
            assert "问题" in data["question"] or "测试问题" in data["question"]

            # Submit 5 answers
            for i in range(5):
                res = client.post("/api/world/answer", json={"answer": f"回答{i}"})
                assert res.status_code == 200
                data = res.json()
                if i < 4:
                    assert data["ok"] is True
                    assert data["complete"] is False
                else:
                    assert data["ok"] is True
                    assert data["complete"] is True
                    assert data["character"]["name"] == "李逍遥"

    def test_load_character(self, tmp_path):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async",
            new_callable=AsyncMock,
        ) as mock_summarize:
            mock_summarize.return_value = World(time="现代", place="上海")
            client.post("/api/create", json={"name": "林月如"})
            for i in range(5):
                r = client.post("/api/world/answer", json={"answer": f"a{i}"})
                if r.json().get("complete"):
                    break

        res = client.post("/api/load", json={"name": "林月如"})
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["character"]["name"] == "林月如"


class TestChatAndActions:
    def test_chat_stream(self):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async",
            new_callable=AsyncMock,
        ) as mock_summarize:
            mock_summarize.return_value = World(time="现代", place="北京")
            client.post("/api/create", json={"name": "阿奴"})
            for i in range(5):
                r = client.post("/api/world/answer", json={"answer": f"a{i}"})
                if r.json().get("complete"):
                    break

        # Now chat
        res = client.post("/api/chat", json={"message": "你好"})
        assert res.status_code == 200
        # SSE response
        text = res.text
        assert "data:" in text
        assert '"type": "done"' in text or "done" in text

    def test_undo(self):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async",
            new_callable=AsyncMock,
        ) as mock_summarize:
            mock_summarize.return_value = World(time="现代", place="广州")
            client.post("/api/create", json={"name": "酒剑仙"})
            for i in range(5):
                r = client.post("/api/world/answer", json={"answer": f"a{i}"})
                if r.json().get("complete"):
                    break

        client.post("/api/chat", json={"message": "测试"})
        res = client.post("/api/undo")
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_story_append_toggle(self):
        with client:
            res = client.post("/api/toggle-story-append", json={"enabled": True})
            assert res.status_code == 200
            assert res.json()["enabled"] is True

    def test_get_story_empty(self):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async",
            new_callable=AsyncMock,
        ) as mock_summarize:
            mock_summarize.return_value = World(time="现代", place="深圳")
            client.post("/api/create", json={"name": "石长老"})
            for i in range(5):
                r = client.post("/api/world/answer", json={"answer": f"a{i}"})
                if r.json().get("complete"):
                    break

        res = client.get("/api/story")
        assert res.status_code == 200
        assert "暂无" in res.text or "故事" in res.text


class TestCharacterManagement:
    def test_delete_and_rename(self):
        with patch(
            "lonely_world.web.api.WorldBuilder.summarize_async",
            new_callable=AsyncMock,
        ) as mock_summarize:
            mock_summarize.return_value = World(time="现代", place="杭州")
            client.post("/api/create", json={"name": "王小虎"})
            for i in range(5):
                r = client.post("/api/world/answer", json={"answer": f"a{i}"})
                if r.json().get("complete"):
                    break

        res = client.post(
            "/api/characters/rename", json={"old_name": "王小虎", "new_name": "王小虎2"}
        )
        assert res.status_code == 200
        assert res.json()["ok"] is True

        res = client.post("/api/characters/delete", json={"name": "王小虎2"})
        assert res.status_code == 200
        assert res.json()["ok"] is True
