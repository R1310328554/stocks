"""条件选股器：估值/成长/质量/技术/资金多条件组合筛选。"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators, detect_patterns


FIELD_LABELS = {
    "pe": "市盈率",
    "pb": "市净率",
    "roe": "ROE",
    "profit_growth": "净利增长%",
    "revenue_growth": "营收增长%",
    "dividend_yield": "股息率%",
    "debt_ratio": "资产负债率%",
    "turnover": "换手率%",
    "ret_20": "20日涨幅%",
    "rsi14": "RSI",
    "vol_ratio": "量比",
    "volatility": "年化波动%",
}


def run_screener(
    filters: list[dict[str, Any]],
    industries: list[str] | None = None,
    require_signals: list[str] | None = None,
    require_patterns: list[str] | None = None,
    sort_by: str = "score",
    limit: int = 30,
) -> dict:
    """filters: [{field, op(gte|lte), value}]"""
    provider = get_data_provider()
    rows = []
    for s in provider.list_stocks(limit=80):
        if industries and s["industry"] not in industries:
            continue
        fund = provider.get_fundamentals(s["ts_code"])
        bars = provider.get_daily_bars(s["ts_code"], days=90)
        ind = compute_indicators(bars)
        patterns = detect_patterns(bars)
        merged = {**fund, **{k: ind.get(k) for k in ("ret_20", "rsi14", "vol_ratio", "volatility", "close", "pct_chg")}}

        ok = True
        for f in filters:
            field, op, value = f.get("field"), f.get("op", "gte"), float(f.get("value", 0))
            v = merged.get(field)
            if v is None:
                continue
            if op == "gte" and float(v) < value:
                ok = False
                break
            if op == "lte" and float(v) > value:
                ok = False
                break
        if not ok:
            continue
        if require_signals and not any(any(k in sig for k in require_signals) for sig in ind.get("signals", [])):
            continue
        if require_patterns and not any(p in patterns for p in require_patterns):
            continue

        # 匹配度得分：各过滤条件的满足裕度 + 质量修正
        score = 60.0
        score += min(15, max(-10, fund["roe"] - 10) * 0.6)
        score += min(10, max(-10, fund["profit_growth"]) * 0.25)
        score += 5 if fund["main_net_inflow"] > 0 else -3
        score += len(patterns) * 3
        score = max(20, min(96, score))

        advice = build_trade_advice(
            close=ind.get("close", 0),
            total_score=score,
            volatility=ind.get("volatility", 22),
            rsi=ind.get("rsi14", 50),
            ret_20=ind.get("ret_20", 0),
        )
        rows.append(
            {
                "ts_code": s["ts_code"],
                "name": s["name"],
                "industry": s["industry"],
                "close": round(float(ind.get("close", 0)), 2),
                "pct_chg": round(float(ind.get("pct_chg", 0)), 2),
                "score": round(score, 1),
                "matched": {
                    FIELD_LABELS.get(f["field"], f["field"]): merged.get(f["field"])
                    for f in filters
                    if f.get("field") in merged
                },
                "signals": ind.get("signals", []),
                "patterns": patterns,
                "advice": advice,
                "pe": fund["pe"],
                "roe": fund["roe"],
                "profit_growth": fund["profit_growth"],
                "turnover": fund["turnover"],
                "ret_20": ind.get("ret_20", 0),
            }
        )

    if sort_by == "score":
        rows.sort(key=lambda x: x["score"], reverse=True)
    elif sort_by in {"pe", "roe", "profit_growth", "ret_20", "turnover"}:
        rows.sort(key=lambda x: x.get(sort_by) or 0, reverse=sort_by != "pe")

    return {
        "trade_date": date.today(),
        "total": len(rows),
        "filters": filters,
        "available_fields": FIELD_LABELS,
        "items": rows[:limit],
    }