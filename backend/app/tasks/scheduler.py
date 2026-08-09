"""定时任务：选股计算、情绪指数、数据质量检查（MVP 内存调度）."""

from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.services.datasources import get_data_provider
from app.services.strategies import MultiFactorPicker

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
_last_runs: dict[str, str] = {}


def get_task_status() -> dict:
    return {"last_runs": _last_runs, "jobs": [j.id for j in scheduler.get_jobs()]}


async def job_daily_picks() -> None:
    logger.info("执行策略选股计算...")
    result = MultiFactorPicker().run(top_n=get_settings().top_n_picks)
    _last_runs["strategy_picks"] = datetime.utcnow().isoformat() + "Z"
    logger.info("选股完成: %s 只", result["total"])


async def job_sentiment() -> None:
    overview = get_data_provider().get_market_overview()
    _last_runs["sentiment_index"] = datetime.utcnow().isoformat() + "Z"
    logger.info("情绪指数: %s (%s)", overview["fear_greed"], overview["fear_greed_label"])


async def job_data_quality() -> None:
    stocks = get_data_provider().list_stocks(limit=10)
    ok = 0
    for s in stocks:
        bars = get_data_provider().get_daily_bars(s["ts_code"], days=30)
        if len(bars) >= 10:
            ok += 1
    _last_runs["data_quality"] = datetime.utcnow().isoformat() + "Z"
    logger.info("数据质量检查: %s/%s 通过", ok, len(stocks))


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.enable_scheduler:
        return
    if scheduler.running:
        return
    scheduler.add_job(job_daily_picks, "cron", hour=18, minute=0, id="strategy_picks")
    scheduler.add_job(job_sentiment, "cron", hour=16, minute=0, id="sentiment_index")
    scheduler.add_job(job_data_quality, "cron", hour=8, minute=0, id="data_quality")
    # 启动时先跑一次，方便演示
    scheduler.add_job(job_daily_picks, "date", run_date=datetime.now(), id="warmup_picks")
    scheduler.start()
    logger.info("调度器已启动")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)