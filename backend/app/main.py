from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import dispose_engine
from app.deps import get_triage_provider
from app.error_handlers import register_error_handlers
from app.routes import complaints, health


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_triage_provider()  # fail fast at startup if TRIAGE_PROVIDER is misconfigured
    yield
    dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="CivicPulse API", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(complaints.router)
    register_error_handlers(app)
    return app


app = create_app()
