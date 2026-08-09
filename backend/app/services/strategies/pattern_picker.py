"""形态选股：经典技术形态扫描。"""

from __future__ import annotations

from datetime import date

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators, detect_patterns


def pick_by_pattern(top_n: int = 15, pattern: str | None = None) -> dict:
    provider = get_data_provider()
    stocks = provider.list_stocks(limit=80)
    hits = []
    for s in stocks:
        bars = provider.get_daily_bars(s["ts_code"], days=120)
        patterns = detect_patterns(bars)
        if not patterns:
            continue
        if pattern and not any(pattern in p for p in patterns):
            continue
        ind = compute_indicators(bars)
        score = 55 + len(patterns) * 12 + (8 if "放量突破" in patterns else 0)
        if ind.get("macd", 0) > 0:
            score += 6
        advice = build_trade_advice(
            close=ind.get("close", 0),
            total_score=score,
            volatility=ind.get("volatility", 25),
            rsi=ind.get("rsi14", 50),
            ret_20=ind.get("ret_20", 0),
            factors={"momentum": score},
        )
        hits.append(
            {
                "rank": 0,
                "ts_code": s["ts_code"],
                "name": s["name"],
                "industry": s["industry"],
                "asset_type": "Stock",
                "total_score": round(float(min(98, score)), 2),
                "factors": {
                    "value": 50.0,
                    "growth": 55.0,
                    "quality": 55.0,
                    "momentum": round(float(min(98, score)), 2),
                    "capital": 50.0,
                    "sentiment": round(float(ind.get("vol_ratio", 1) * 35), 2),
                },
                "reason": "识别形态：" + "、".join(patterns),
                "close": ind.get("close"),
                "pct_chg": ind.get("pct_chg"),
                "patterns": patterns,
                "advice": advice,
            }
        )

    hits.sort(key=lambda x: x["total_score"], reverse=True)
    for i, item in enumerate(hits[:top_n]):
        item["rank"] = i + 1
    return {
        "trade_date": date.today(),
        "strategy": "pattern_scan",
        "data_source": provider.source_name,
        "total": min(top_n, len(hits)),
        "items": hits[:top_n],
    }