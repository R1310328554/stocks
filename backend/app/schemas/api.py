"""API 响应/请求模型."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class StockBrief(BaseModel):
    ts_code: str
    symbol: str
    name: str
    industry: str
    market: str = ""
    asset_type: str = "Stock"
    close: float | None = None
    pct_chg: float | None = None


class FactorBreakdown(BaseModel):
    value: float
    growth: float
    quality: float
    momentum: float
    capital: float
    sentiment: float


class TradeAdvice(BaseModel):
    action: str
    confidence: str
    hold_horizon: str
    hold_days_min: int
    hold_days_max: int
    position_advice: str
    entry_price: float
    stop_loss_pct: float
    take_profit_pct: float
    stop_loss_price: float
    take_profit_price: float
    trailing_stop_pct: float
    checklist: list[str] = Field(default_factory=list)
    risk_note: str = ""


class PickItem(BaseModel):
    rank: int
    ts_code: str
    name: str
    industry: str
    asset_type: str = "Stock"
    total_score: float
    factors: FactorBreakdown
    reason: str
    close: float | None = None
    pct_chg: float | None = None
    pe: float | None = None
    pb: float | None = None
    roe: float | None = None
    manager: str | None = None
    metrics: dict[str, Any] | None = None
    themes: list[str] | None = None
    patterns: list[str] | None = None
    dimensions: dict[str, Any] | None = None
    advice: TradeAdvice | None = None


class PickListResponse(BaseModel):
    trade_date: date
    strategy: str
    data_source: str
    total: int
    items: list[PickItem]
    asset_type: str | None = None
    methodology: str | None = None
    market_hot_sectors: list[dict[str, Any]] | None = None


class DiagnosisSection(BaseModel):
    score: float
    level: str
    summary: str
    details: list[str] = Field(default_factory=list)


class DiagnosisReport(BaseModel):
    ts_code: str
    name: str
    industry: str
    trade_date: date
    overall_score: float
    overall_level: str
    fundamental: DiagnosisSection
    technical: DiagnosisSection
    capital: DiagnosisSection
    sentiment: DiagnosisSection | None = None
    layers: dict[str, str] | None = None
    risks: list[str]
    signals: list[str]
    advice: TradeAdvice | None = None
    indicators: dict[str, Any]


class MarketOverview(BaseModel):
    trade_date: date
    data_source: str
    index_summary: list[dict[str, Any]]
    hot_sectors: list[dict[str, Any]]
    limit_up_count: int
    limit_down_count: int
    northbound_net: float
    margin_balance_change: float
    fear_greed: float
    fear_greed_label: str
    commentary: str


class CapitalFlowSignal(BaseModel):
    ts_code: str
    name: str
    margin_signal: str
    northbound_signal: str
    block_trade_signal: str
    consensus: str
    crowding_percentile: float
    summary: str


class SignalItem(BaseModel):
    ts_code: str
    name: str
    signal_type: str
    direction: str
    strength: float
    description: str
    generated_at: datetime


class TimingSignalsResponse(BaseModel):
    trade_date: date
    items: list[SignalItem]


class WatchItemCreate(BaseModel):
    ts_code: str
    name: str = ""
    group_name: str = "默认"
    note: str = ""


class WatchItemOut(BaseModel):
    id: int
    ts_code: str
    name: str
    group_name: str
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NaturalLanguagePickRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_n: int = Field(default=15, ge=1, le=50)


class AlertItem(BaseModel):
    id: str
    ts_code: str
    name: str
    alert_type: str
    message: str
    severity: str
    created_at: datetime


class BacktestRequest(BaseModel):
    strategy: str = "multi_factor"
    start_date: str | None = None
    end_date: str | None = None
    top_n: int = 10


class BacktestReport(BaseModel):
    strategy: str
    start_date: date
    end_date: date
    total_return: float
    max_drawdown: float
    win_rate: float
    sharpe: float
    equity_curve: list[dict[str, Any]]
    commentary: str


class PortfolioHoldingIn(BaseModel):
    ts_code: str
    weight: float | None = None
    cost: float | None = None


class PortfolioRequest(BaseModel):
    holdings: list[PortfolioHoldingIn] = Field(default_factory=list)


class AgentRequest(BaseModel):
    ts_code: str | None = None
    question: str = ""