"""Tests for retry wrapper."""

import pytest

from lonely_world.llm.retry import _classify_error, _is_retriable, with_retry, with_retry_async


class FakeRetriableError(Exception):
    pass


class FakeFatalError(Exception):
    pass


class TestIsRetriable:
    def test_retriable_names(self):
        assert _is_retriable(Exception("x")) is False
        assert _is_retriable(type("RateLimitError", (Exception,), {})("x")) is True
        assert _is_retriable(type("APIConnectionError", (Exception,), {})("x")) is True
        assert _is_retriable(type("TimeoutError", (Exception,), {})("x")) is True
        assert _is_retriable(ConnectionError("x")) is True


class TestClassifyError:
    def test_auth_error(self):
        exc = type("AuthenticationError", (Exception,), {})("bad key")
        assert "API Key" in _classify_error(exc)

    def test_rate_limit(self):
        exc = type("RateLimitError", (Exception,), {})("too fast")
        assert "频率超限" in _classify_error(exc)

    def test_generic(self):
        exc = ValueError("unknown")
        assert "API 调用失败" in _classify_error(exc)

    def test_timeout_error(self):
        exc = type("APITimeoutError", (Exception,), {})("slow")
        assert "超时" in _classify_error(exc)

    def test_connection_error(self):
        exc = type("ConnectTimeout", (Exception,), {})("net")
        assert "连接" in _classify_error(exc)

    def test_bad_request_error(self):
        exc = type("BadRequestError", (Exception,), {})("bad")
        assert "参数错误" in _classify_error(exc)


class TestWithRetry:
    def test_success_no_retry(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert func() == "ok"
        assert call_count == 1

    def test_retriable_then_success(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("network")
            return "ok"

        assert func() == "ok"
        assert call_count == 2

    def test_retriable_exhausted(self):
        call_count = 0

        @with_retry(max_retries=1, base_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("network")

        with pytest.raises(ConnectionError):
            func()
        assert call_count == 2

    def test_non_retriable_raises_immediately(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("fatal")

        with pytest.raises(ValueError):
            func()
        assert call_count == 1


class TestWithRetryAsync:
    @pytest.mark.anyio
    async def test_async_success_no_retry(self):
        call_count = 0

        @with_retry_async(max_retries=2, base_delay=0.01)
        async def func():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert await func() == "ok"
        assert call_count == 1

    @pytest.mark.anyio
    async def test_async_retriable_then_success(self):
        call_count = 0

        @with_retry_async(max_retries=2, base_delay=0.01)
        async def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("network")
            return "ok"

        assert await func() == "ok"
        assert call_count == 2

    @pytest.mark.anyio
    async def test_async_retriable_exhausted(self):
        call_count = 0

        @with_retry_async(max_retries=1, base_delay=0.01)
        async def func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("network")

        with pytest.raises(ConnectionError):
            await func()
        assert call_count == 2

    @pytest.mark.anyio
    async def test_async_non_retriable_raises_immediately(self):
        call_count = 0

        @with_retry_async(max_retries=2, base_delay=0.01)
        async def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("fatal")

        with pytest.raises(ValueError):
            await func()
        assert call_count == 1
