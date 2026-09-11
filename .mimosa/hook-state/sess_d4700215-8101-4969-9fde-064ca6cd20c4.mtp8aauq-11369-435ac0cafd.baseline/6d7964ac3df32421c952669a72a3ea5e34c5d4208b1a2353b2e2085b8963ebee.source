"""Retry wrapper for LLM API calls with backoff and error classification."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Optional

logger = logging.getLogger(__name__)

RETRIABLE_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
)


def _is_retriable(exc: Exception) -> bool:
    """Determine if an exception is worth retrying."""
    name = type(exc).__name__
    # Common network/timeout error names across SDKs
    if name in {
        "APIConnectionError",
        "APITimeoutError",
        "TimeoutError",
        "ConnectionError",
        "ConnectTimeout",
        "ReadTimeout",
    }:
        return True
    # Rate limit is retriable
    if name in {"RateLimitError"}:
        return True
    return isinstance(exc, RETRIABLE_NETWORK_ERRORS)


def _classify_error(exc: Exception) -> str:
    """Return a user-friendly classification string."""
    name = type(exc).__name__
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return "认证失败，请检查 API Key 是否有效。"
    if name in {"RateLimitError"}:
        return "API 调用频率超限，请稍后重试。"
    if name in {"APIConnectionError", "ConnectionError", "ConnectTimeout"}:
        return "无法连接到 API 服务，请检查网络和 Base URL。"
    if name in {"APITimeoutError", "TimeoutError", "ReadTimeout"}:
        return "请求超时，可能是网络不稳定或模型响应较慢。"
    if name in {"BadRequestError"}:
        return "请求参数错误，请检查模型名称或上下文长度。"
    return f"API 调用失败（{name}）"


def with_retry(
    max_retries: int = 2,
    base_delay: float = 1.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator that retries retriable exceptions with exponential backoff."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries and _is_retriable(exc):
                        delay = base_delay * (2**attempt)
                        msg = f"调用失败，{delay:.1f} 秒后重试（第 {attempt + 1}/{max_retries} 次）: {exc}"
                        logger.warning(msg)
                        if on_retry:
                            on_retry(exc, attempt + 1)
                        time.sleep(delay)
                        continue
                    raise
            # Should never reach here, but satisfy type checker
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def with_retry_async(
    max_retries: int = 2,
    base_delay: float = 1.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Async decorator that retries retriable exceptions with exponential backoff."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries and _is_retriable(exc):
                        delay = base_delay * (2**attempt)
                        msg = f"调用失败，{delay:.1f} 秒后重试（第 {attempt + 1}/{max_retries} 次）: {exc}"
                        logger.warning(msg)
                        if on_retry:
                            on_retry(exc, attempt + 1)
                        await __import__("asyncio").sleep(delay)
                        continue
                    raise
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
