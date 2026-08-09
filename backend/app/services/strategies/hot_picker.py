"""热点/连板/主题/资金四维选股。"""

from __future__ import annotations

from datetime import date

import numpy as np

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators


THEME_KEYWORDS = {
    "人工智能": ["人工智能", "软件", "计算机", "半导体"],
    "新能源": ["光伏", "电池", "锂电", "汽车"],
    "消费复苏": ["白酒", "食品", "免税"],
    "高端制造": ["机械", "工控", "电子"],
}


def pick_hot(top_n: int = 15) -> dict:
    provider = get_data_provider()
    overview = provider.get_market_overview()
    hot_names = [s["name"] for s in overview.get("hot_sectors", [])]
    stocks = provider.list_stocks(limit=80)
    scored = []

    for s in stocks:
        fund = provider.get_fundamentals(s["ts_code"])
        bars = provider.get_daily_bars(s["ts_code"], days=60)
        ind = compute_indicators(bars)
        theme_hit = 0
        themes = []
        for theme, inds in THEME_KEYWORDS.items():
            if s["industry"] in inds or any(t in hot_names for t in [theme] if theme[:2] in "".join(hot_names)):
                if s["industry"] in inds:
                    theme_hit += 1
                    themes.append(theme)
        # 简化：行业出现在热点前列加分
        for i, h in enumerate(hot_names):
            if h in s["industry"] or s["industry"] in h:
                theme_hit += max(0, 6 - i)
                themes.append(h)

        limit_like = 1 if ind.get("pct_chg", 0) >= 7 else 0
        capital = 1 if fund["main_net_inflow"] > 0 else 0
        north = 1 if fund["northbound_change"] > 0 else 0
        score = (
            theme_hit * 12
            + ind.get("ret_5", 0) * 1.2
            + ind.get("vol_ratio", 1) * 8
            + capital * 10
            + north * 8
            + limit_like * 15
            + max(0, 30 - abs(ind.get("rsi14", 50) - 55))
        )
        advice = build_trade_advice(
            close=ind.get("close", 0),
            total_score=min(99, score),
            volatility=ind.get("volatility", 25),
            rsi=ind.get("rsi14", 50),
            ret_20=ind.get("ret_20", 0),
            factors={"momentum": min(99, score), "capital": 60 + capital * 20 + north * 10},
        )
        scored.append(
            {
                "rank": 0,
                "ts_code": s["ts_code"],
                "name": s["name"],
                "industry": s["industry"],
                "asset_type": "Stock",
                "total_score": round(float(min(99, score)), 2),
                "factors": {
                    "value": 50.0,
                    "growth": round(float(50 + ind.get("ret_20", 0)), 2),
                    "quality": 55.0,
                    "momentum": round(float(min(99, 50 + ind.get("ret_5", 0) * 3)), 2),
                    "capital": round(60 + capital * 20 + north * 10, 2),
                    "sentiment": round(float(min(99, ind.get("vol_ratio", 1) * 40)), 2),
                },
                "reason": f"主题 {','.join(themes[:2]) or '轮动'}；量能比 {ind.get('vol_ratio')}；主力{'流入' if capital else '观望'}",
                "close": ind.get("close"),
                "pct_chg": ind.get("pct_chg"),
                "themes": themes[:3],
                "dimensions": {
                    "theme": theme_hit,
                    "limit_board": limit_like,
                    "capital": capital + north,
                    "heat": round(float(ind.get("vol_ratio", 1)), 2),
                },
                "advice": advice,
            }
        )

    scored.sort(key=lambda x: x["total_score"], reverse=True)
    for i, item in enumerate(scored[:top_n]):
        item["rank"] = i + 1

    return {
        "trade_date": date.today(),
        "strategy": "hot_theme_capital",
        "data_source": provider.source_name,
        "total": min(top_n, len(scored)),
        "items": scored[:top_n],
        "market_hot_sectors": overview.get("hot_sectors", []),
    }