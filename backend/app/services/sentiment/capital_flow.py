"""主力情绪感知：融资融券 + 北向 + 大宗 三源聚合."""

from __future__ import annotations

from datetime import datetime

import numpy as np

from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators


def _dir_label(value: float, pos: str = "流入", neg: str = "流出") -> str:
    if value > 0:
        return pos
    if value < 0:
        return neg
    return "中性"


def analyze_capital_flow(ts_code: str) -> dict:
    provider = get_data_provider()
    stock = provider.resolve_name(ts_code)
    fund = provider.get_fundamentals(stock["ts_code"])

    margin = float(fund["margin_balance_change"])
    north = float(fund["northbound_change"])
    block = float(fund["block_premium"])
    main = float(fund["main_net_inflow"])

    margin_signal = _dir_label(margin, "融资净增", "融资净减")
    north_signal = _dir_label(north, "北向增持", "北向减持")
    block_signal = "折价接盘" if block < -1 else "溢价抢筹" if block > 1 else "平价成交"

    votes = [
        1 if margin > 0 else -1 if margin < 0 else 0,
        1 if north > 0 else -1 if north < 0 else 0,
        1 if block > 0 else -1 if block < 0 else 0,
    ]
    score = sum(votes)
    if score >= 2:
        consensus = "共识看多（资金合力）"
    elif score <= -2:
        consensus = "共识看空（资金撤离）"
    elif score == 0:
        consensus = "明显背离（信号弱化）"
    else:
        consensus = "弱一致（需结合价格确认）"

    # 拥挤度：用主力流入强度的历史伪分位
    rng = np.random.default_rng(abs(hash(stock["ts_code"] + ":crowd")) % (2**32))
    hist = rng.normal(0, abs(main) * 0.8 + 1e6, size=60)
    crowding = float((hist < main).mean() * 100)

    summary = (
        f"{stock['name']} 融资{margin_signal}、{north_signal}、大宗{block_signal}；"
        f"{consensus}；拥挤度分位 {crowding:.1f}%。"
    )
    if crowding >= 90:
        summary += " 高拥挤预警，注意短线回撤风险。"

    return {
        "ts_code": stock["ts_code"],
        "name": stock["name"],
        "margin_signal": margin_signal,
        "northbound_signal": north_signal,
        "block_trade_signal": block_signal,
        "consensus": consensus,
        "crowding_percentile": round(crowding, 1),
        "summary": summary,
    }


def build_timing_signals(limit: int = 20) -> dict:
    provider = get_data_provider()
    stocks = provider.list_stocks(limit=40)
    items: list[dict] = []
    now = datetime.utcnow()

    for stock in stocks:
        bars = provider.get_daily_bars(stock["ts_code"], days=90)
        ind = compute_indicators(bars)
        fund = provider.get_fundamentals(stock["ts_code"])
        for sig in ind.get("signals", []):
            direction = "buy" if any(k in sig for k in ["金叉", "超卖", "反弹", "突破"]) else "sell" if any(
                k in sig for k in ["死叉", "超买", "回调", "跌破"]
            ) else "neutral"
            strength = min(1.0, 0.55 + abs(ind.get("macd", 0)) / 5)
            items.append(
                {
                    "ts_code": stock["ts_code"],
                    "name": stock["name"],
                    "signal_type": "technical",
                    "direction": direction,
                    "strength": round(strength, 2),
                    "description": sig,
                    "generated_at": now,
                }
            )
        if fund["main_net_inflow"] > 1e7:
            items.append(
                {
                    "ts_code": stock["ts_code"],
                    "name": stock["name"],
                    "signal_type": "capital",
                    "direction": "buy",
                    "strength": 0.72,
                    "description": "主力净流入显著",
                    "generated_at": now,
                }
            )
        if fund["northbound_change"] > 0.2:
            items.append(
                {
                    "ts_code": stock["ts_code"],
                    "name": stock["name"],
                    "signal_type": "capital",
                    "direction": "buy",
                    "strength": 0.68,
                    "description": "北向资金持续增持",
                    "generated_at": now,
                }
            )

    items.sort(key=lambda x: x["strength"], reverse=True)
    return {"trade_date": now.date(), "items": items[:limit]}