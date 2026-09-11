"""FastAPI application entry point for the lonely-world Web UI."""

import contextlib
import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from lonely_world.logging_config import setup_logging
from lonely_world.web.api import router as api_router
from lonely_world.web.session import WebConfigError, store

SESSION_SECRET = os.getenv("LONELY_WORLD_SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError(
        "LONELY_WORLD_SESSION_SECRET environment variable is not set. "
        "Please set it to a secure random string before running the web server."
    )


def get_client_ip(request: Request) -> str:
    """Get client IP, considering proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(verbose=False)
    try:
        store.load_server_config()
    except WebConfigError as exc:
        logger = logging.getLogger(__name__)
        logger.error("Server config error: %s", exc)
    yield


app = FastAPI(title="lonely-world", version="0.2.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Static files
app.mount("/static", StaticFiles(directory="web_static"), name="static")

# API routes
app.include_router(api_router)


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/static/index.html")


def run() -> None:
    uvicorn.run("lonely_world.web.main:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    run()
