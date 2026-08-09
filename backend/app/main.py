"""智选投 API 入口."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.tasks.scheduler import get_task_status, start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("zhixuantou")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    start_scheduler()
    logger.info("智选投后端已启动")
    yield
    stop_scheduler()
    logger.info("智选投后端已关闭")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="面向经验不足、资金有限用户的智能选股平台 MVP",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "api": settings.api_prefix,
            "tasks": get_task_status(),
        }

    return app


app = create_app()