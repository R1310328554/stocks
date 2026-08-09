"""API 路由聚合：股票 / 多资产 / 诊股 / 实时 / Agent / 组合."""

from __future__ import annotations

import asyncio
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import PickResult, WatchItem
from app.schemas.api import (
    AgentRequest,
    BacktestReport,
    BacktestRequest,
    CapitalFlowSignal,
    DiagnosisReport,
    MarketOverview,
    NaturalLanguagePickRequest,
    PickListResponse,
    PortfolioRequest,
    TimingSignalsResponse,
    WatchItemCreate,
    WatchItemOut,
)
from pydantic import BaseModel, Field

from app.services.agents import run_multi_agent_research
from app.services.backtest import run_backtest
from app.services.marketdata.datacenter import (
    company_profile,
    dragon_tiger,
    event_calendar,
    kline,
    limit_up_pool,
    rankings,
    research_reports,
    sector_heatmap,
)
from app.services.strategies.screener import run_screener
from app.services.strategies.strategy_center import list_strategies, run_strategy
from app.services.trading.paper import account_state, place_order, reset_account
from app.services.datasources import get_data_provider
from app.services.datasources.multi_asset import list_assets
from app.services.datasources.source_registry import source_health
from app.services.diagnosis import diagnose_stock
from app.services.portfolio import analyze_portfolio
from app.services.realtime import quote_snapshot
from app.services.sentiment import analyze_capital_flow, build_timing_signals
from app.services.strategies import MultiFactorPicker, parse_natural_language_filters
from app.services.strategies.asset_recommender import AssetRecommender
from app.services.strategies.hot_picker import pick_hot
from app.services.strategies.pattern_picker import pick_by_pattern
from app.tasks.scheduler import get_task_status

api_router = APIRouter()


@api_router.get("/health")
async def health() -> dict:
    settings = get_settings()
    provider = get_data_provider()
    return {
        "status": "ok",
        "app": settings.app_name,
        "data_source": provider.source_name,
        "data_mode": settings.data_mode,
        "version": "0.2.0",
        "features": [
            "multi_factor",
            "hot_pick",
            "pattern_pick",
            "nl_pick",
            "diagnosis",
            "trade_advice",
            "etf_fund_lof_bond",
            "agents",
            "portfolio",
            "realtime",
        ],
    }


@api_router.get("/meta/sources")
async def meta_sources() -> dict:
    settings = get_settings()
    return source_health(live_enabled=settings.use_live_data)


@api_router.get("/meta/tasks")
async def meta_tasks() -> dict:
    return get_task_status()


@api_router.get("/market/overview", response_model=MarketOverview)
async def market_overview() -> MarketOverview:
    data = get_data_provider().get_market_overview()
    return MarketOverview(**data)


@api_router.get("/stocks")
async def list_stocks(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    rows = get_data_provider().list_stocks(limit=limit)
    return {"total": len(rows), "items": rows}


@api_router.get("/assets")
async def assets(
    asset_type: str | None = Query(default=None, description="stock|etf|lof|fund|bond"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    rows = list_assets(asset_type=asset_type, limit=limit)
    return {"total": len(rows), "items": rows}


@api_router.get("/picks/daily", response_model=PickListResponse)
async def daily_picks(
    top_n: int = Query(default=20, ge=1, le=50),
    industry: str | None = None,
    persist: bool = False,
    db: AsyncSession = Depends(get_db),
) -> PickListResponse:
    picker = MultiFactorPicker()
    industries = [industry] if industry else None
    result = picker.run(top_n=top_n, industries=industries)
    if persist and result["items"]:
        for item in result["items"]:
            db.add(
                PickResult(
                    trade_date=result["trade_date"],
                    ts_code=item["ts_code"],
                    name=item["name"],
                    industry=item["industry"],
                    rank=item["rank"],
                    total_score=item["total_score"],
                    value_score=item["factors"]["value"],
                    growth_score=item["factors"]["growth"],
                    quality_score=item["factors"]["quality"],
                    momentum_score=item["factors"]["momentum"],
                    capital_score=item["factors"]["capital"],
                    sentiment_score=item["factors"]["sentiment"],
                    reason=item["reason"],
                )
            )
        await db.commit()
    return PickListResponse(**result)


@api_router.get("/picks/hot", response_model=PickListResponse)
async def hot_picks(top_n: int = Query(default=15, ge=1, le=50)) -> PickListResponse:
    return PickListResponse(**pick_hot(top_n=top_n))


@api_router.get("/picks/pattern", response_model=PickListResponse)
async def pattern_picks(
    top_n: int = Query(default=15, ge=1, le=50),
    pattern: str | None = None,
) -> PickListResponse:
    return PickListResponse(**pick_by_pattern(top_n=top_n, pattern=pattern))


@api_router.post("/picks/natural", response_model=PickListResponse)
async def natural_picks(body: NaturalLanguagePickRequest) -> PickListResponse:
    filters = parse_natural_language_filters(body.query)
    picker = MultiFactorPicker()
    result = picker.run(
        top_n=filters.get("top_n", body.top_n),
        industries=filters.get("industries"),
        max_pe=filters.get("max_pe"),
        min_roe=filters.get("min_roe"),
        min_profit_growth=filters.get("min_profit_growth"),
        require_patterns=filters.get("require_patterns"),
        market=filters.get("market"),
    )
    result["strategy"] = "natural_language"
    return PickListResponse(**result)


@api_router.get("/recommend/{asset_type}", response_model=PickListResponse)
async def recommend_assets(
    asset_type: str,
    top_n: int = Query(default=10, ge=1, le=50),
    style: str | None = None,
) -> PickListResponse:
    if asset_type.lower() not in {"etf", "lof", "fund", "bond"}:
        raise HTTPException(status_code=400, detail="asset_type 需为 etf|lof|fund|bond")
    result = AssetRecommender().recommend(asset_type=asset_type, top_n=top_n, style=style)
    return PickListResponse(**result)


@api_router.get("/diagnosis/{ts_code}", response_model=DiagnosisReport)
async def diagnosis(ts_code: str) -> DiagnosisReport:
    report = diagnose_stock(ts_code)
    return DiagnosisReport(**report)


@api_router.get("/capital-flow/{ts_code}", response_model=CapitalFlowSignal)
async def capital_flow(ts_code: str) -> CapitalFlowSignal:
    return CapitalFlowSignal(**analyze_capital_flow(ts_code))


@api_router.get("/signals/timing", response_model=TimingSignalsResponse)
async def timing_signals(limit: int = Query(default=20, ge=1, le=100)) -> TimingSignalsResponse:
    return TimingSignalsResponse(**build_timing_signals(limit=limit))


@api_router.get("/news")
async def news(limit: int = Query(default=20, ge=1, le=50)) -> dict:
    return {"items": get_data_provider().get_news(limit=limit)}


@api_router.get("/alerts")
async def alerts(limit: int = Query(default=15, ge=1, le=50)) -> dict:
    return {"items": get_data_provider().get_alerts(limit=limit)}


@api_router.get("/quotes")
async def quotes(codes: str | None = None, limit: int = Query(default=30, ge=1, le=100)) -> dict:
    code_list = [c.strip() for c in codes.split(",")] if codes else None
    return quote_snapshot(codes=code_list, limit=limit)


@api_router.websocket("/ws/quotes")
async def ws_quotes(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = quote_snapshot(limit=20)
            await websocket.send_text(json.dumps(payload, ensure_ascii=False))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001
        await websocket.close()


@api_router.get("/watchlist", response_model=list[WatchItemOut])
async def get_watchlist(db: AsyncSession = Depends(get_db)) -> list[WatchItem]:
    result = await db.execute(select(WatchItem).order_by(WatchItem.created_at.desc()))
    return list(result.scalars().all())


@api_router.post("/watchlist", response_model=WatchItemOut)
async def add_watch(item: WatchItemCreate, db: AsyncSession = Depends(get_db)) -> WatchItem:
    provider = get_data_provider()
    meta = provider.resolve_name(item.ts_code)
    entity = WatchItem(
        ts_code=meta["ts_code"],
        name=item.name or meta["name"],
        group_name=item.group_name,
        note=item.note,
    )
    db.add(entity)
    try:
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"添加失败: {exc}") from exc
    await db.refresh(entity)
    return entity


@api_router.delete("/watchlist/{item_id}")
async def delete_watch(item_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(WatchItem).where(WatchItem.id == item_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="未找到自选")
    await db.delete(entity)
    await db.commit()
    return {"ok": True}


@api_router.post("/backtest", response_model=BacktestReport)
async def backtest(body: BacktestRequest) -> BacktestReport:
    report = run_backtest(strategy=body.strategy, top_n=body.top_n)
    return BacktestReport(**report)


@api_router.post("/portfolio/analyze")
async def portfolio_analyze(body: PortfolioRequest) -> dict:
    holdings = [h.model_dump() for h in body.holdings]
    return analyze_portfolio(holdings)


@api_router.post("/agents/research")
async def agents_research(body: AgentRequest) -> dict:
    return run_multi_agent_research(ts_code=body.ts_code, question=body.question)


# ---------- 数据中心 ----------


@api_router.get("/datacenter/rankings")
async def dc_rankings(
    kind: str = Query(default="gainers", description="gainers|losers|turnover|vol_ratio|inflow|amount"),
    limit: int = Query(default=15, ge=1, le=50),
) -> dict:
    return rankings(kind=kind, limit=limit)


@api_router.get("/datacenter/limit-up")
async def dc_limit_up() -> dict:
    return limit_up_pool()


@api_router.get("/datacenter/dragon-tiger")
async def dc_dragon_tiger(limit: int = Query(default=12, ge=1, le=30)) -> dict:
    return dragon_tiger(limit=limit)


@api_router.get("/datacenter/heatmap")
async def dc_heatmap() -> dict:
    return sector_heatmap()


@api_router.get("/datacenter/calendar")
async def dc_calendar(days: int = Query(default=10, ge=1, le=30)) -> dict:
    return event_calendar(days=days)


@api_router.get("/datacenter/reports")
async def dc_reports(ts_code: str | None = None, limit: int = Query(default=12, ge=1, le=30)) -> dict:
    return research_reports(ts_code=ts_code, limit=limit)


@api_router.get("/stock/{ts_code}/profile")
async def stock_profile(ts_code: str) -> dict:
    return company_profile(ts_code)


@api_router.get("/stock/{ts_code}/kline")
async def stock_kline(ts_code: str, days: int = Query(default=120, ge=20, le=250)) -> dict:
    return kline(ts_code, days=days)


# ---------- 筛选器与策略中心 ----------


class ScreenerFilter(BaseModel):
    field: str
    op: str = "gte"
    value: float


class ScreenerRequest(BaseModel):
    filters: list[ScreenerFilter] = Field(default_factory=list)
    industries: list[str] | None = None
    require_signals: list[str] | None = None
    require_patterns: list[str] | None = None
    sort_by: str = "score"
    limit: int = Field(default=30, ge=1, le=100)


@api_router.post("/screener/run")
async def screener_run(body: ScreenerRequest) -> dict:
    return run_screener(
        filters=[f.model_dump() for f in body.filters],
        industries=body.industries,
        require_signals=body.require_signals,
        require_patterns=body.require_patterns,
        sort_by=body.sort_by,
        limit=body.limit,
    )


@api_router.get("/strategies")
async def strategies_list() -> dict:
    return list_strategies()


@api_router.get("/strategies/{strategy_id}/run")
async def strategies_run(strategy_id: str, top_n: int = Query(default=10, ge=1, le=30)) -> dict:
    try:
        return run_strategy(strategy_id, top_n=top_n)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------- 模拟交易 ----------


class PaperOrderRequest(BaseModel):
    ts_code: str
    side: str = Field(pattern="^(buy|sell)$")
    shares: int = Field(ge=100)


@api_router.get("/paper/account")
async def paper_account(db: AsyncSession = Depends(get_db)) -> dict:
    return await account_state(db)


@api_router.post("/paper/order")
async def paper_order(body: PaperOrderRequest, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        return await place_order(db, body.ts_code, body.side, body.shares)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.post("/paper/reset")
async def paper_reset(db: AsyncSession = Depends(get_db)) -> dict:
    return await reset_account(db)


@api_router.get("/reports/daily")
async def daily_report() -> dict:
    provider = get_data_provider()
    overview = provider.get_market_overview()
    picks = MultiFactorPicker().run(top_n=10)
    hot = pick_hot(top_n=8)
    etf = AssetRecommender().recommend("etf", top_n=5)
    signals = build_timing_signals(limit=10)
    return {
        "trade_date": date.today().isoformat(),
        "market": overview,
        "top_picks": picks["items"],
        "hot_picks": hot["items"],
        "etf_picks": etf["items"],
        "timing_signals": signals["items"],
        "alerts": provider.get_alerts(limit=8),
        "sources": source_health(live_enabled=get_settings().use_live_data),
    }