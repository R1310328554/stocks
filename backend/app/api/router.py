"""API 路由聚合."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import PickResult, WatchItem
from app.schemas.api import (
    BacktestReport,
    BacktestRequest,
    CapitalFlowSignal,
    DiagnosisReport,
    MarketOverview,
    NaturalLanguagePickRequest,
    PickListResponse,
    TimingSignalsResponse,
    WatchItemCreate,
    WatchItemOut,
)
from app.services.backtest import run_backtest
from app.services.datasources import get_data_provider
from app.services.diagnosis import diagnose_stock
from app.services.sentiment import analyze_capital_flow, build_timing_signals
from app.services.strategies import MultiFactorPicker, parse_natural_language_filters

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
    }


@api_router.get("/market/overview", response_model=MarketOverview)
async def market_overview() -> MarketOverview:
    data = get_data_provider().get_market_overview()
    return MarketOverview(**data)


@api_router.get("/stocks")
async def list_stocks(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    rows = get_data_provider().list_stocks(limit=limit)
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


@api_router.get("/reports/daily")
async def daily_report() -> dict:
    provider = get_data_provider()
    overview = provider.get_market_overview()
    picks = MultiFactorPicker().run(top_n=10)
    signals = build_timing_signals(limit=10)
    return {
        "trade_date": date.today().isoformat(),
        "market": overview,
        "top_picks": picks["items"],
        "timing_signals": signals["items"],
        "alerts": provider.get_alerts(limit=8),
    }