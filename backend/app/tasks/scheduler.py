"""定时任务：对齐 README 采集/计算节奏（演示调度）。"""

from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.services.datasources import get_data_provider
from app.services.datasources.source_registry import source_health
from app.services.realtime import quote_snapshot
from app.services.strategies import MultiFactorPicker
from app.services.strategies.asset_recommender import AssetRecommender
from app.services.strategies.hot_picker import pick_hot

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
_last_runs: dict[str, str] = {}


def get_task_status() -> dict:
    return {"last_runs": _last_runs, "jobs": [j.id for j in scheduler.get_jobs()]}


def _mark(name: str) -> None:
    _last_runs[name] = datetime.utcnow().isoformat() + "Z"


async def job_daily_picks() -> None:
    logger.info("执行策略选股计算...")
    result = MultiFactorPicker().run(top_n=get_settings().top_n_picks)
    hot = pick_hot(top_n=10)
    etf = AssetRecommender().recommend("etf", top_n=5)
    _mark("strategy_picks")
    _mark("hot_picks")
    _mark("etf_recommend")
    logger.info("选股完成: 股票%s / 热点%s / ETF%s", result["total"], hot["total"], etf["total"])


async def job_sentiment() -> None:
    overview = get_data_provider().get_market_overview()
    _mark("sentiment_index")
    logger.info("情绪指数: %s (%s)", overview["fear_greed"], overview["fear_greed_label"])


async def job_data_quality() -> None:
    stocks = get_data_provider().list_stocks(limit=10)
    ok = 0
    for s in stocks:
        bars = get_data_provider().get_daily_bars(s["ts_code"], days=30)
        if len(bars) >= 10:
            ok += 1
    health = source_health(live_enabled=get_settings().use_live_data)
    _mark("data_quality")
    logger.info("数据质量: %s/%s；源可靠分 %s", ok, len(stocks), health["reliability_score"])


async def job_news_alerts() -> None:
    provider = get_data_provider()
    news = provider.get_news(limit=5)
    alerts = provider.get_alerts(limit=5)
    _mark("news_fetch")
    _mark("alert_scan")
    logger.info("资讯%s条 / 异动%s条", len(news), len(alerts))


async def job_quotes_heartbeat() -> None:
    snap = quote_snapshot(limit=10)
    _mark("realtime_quotes")
    logger.info("行情心跳: %s 标的", len(snap["items"]))


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.enable_scheduler:
        return
    if scheduler.running:
        return
    scheduler.add_job(job_daily_picks, "cron", hour=18, minute=0, id="strategy_picks")
    scheduler.add_job(job_sentiment, "cron", hour=16, minute=0, id="sentiment_index")
    scheduler.add_job(job_data_quality, "cron", hour=8, minute=0, id="data_quality")
    scheduler.add_job(job_news_alerts, "interval", minutes=10, id="news_alerts")
    scheduler.add_job(job_quotes_heartbeat, "interval", minutes=5, id="quotes_heartbeat")
    scheduler.add_job(job_daily_picks, "date", run_date=datetime.now(), id="warmup_picks")
    scheduler.start()
    logger.info("调度器已启动")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)