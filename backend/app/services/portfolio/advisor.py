"""持仓诊断与组合建议。"""

from __future__ import annotations

from datetime import date

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.datasources.multi_asset import resolve_asset
from app.services.diagnosis import diagnose_stock
from app.services.indicators.technical import compute_indicators


def analyze_portfolio(holdings: list[dict]) -> dict:
    """holdings: [{ts_code, weight?, cost?}]"""
    provider = get_data_provider()
    if not holdings:
        holdings = [
            {"ts_code": "600519.SH", "weight": 0.35, "cost": None},
            {"ts_code": "510300.SH", "weight": 0.4, "cost": None},
            {"ts_code": "019740.SH", "weight": 0.25, "cost": None},
        ]

    details = []
    total_w = sum(float(h.get("weight") or 0) for h in holdings) or 1.0
    score_acc = 0.0
    for h in holdings:
        meta = resolve_asset(h["ts_code"])
        w = float(h.get("weight") or (1 / len(holdings))) / total_w
        bars = provider.get_daily_bars(meta["ts_code"], days=90)
        ind = compute_indicators(bars)
        atype = meta.get("asset_type") or "Stock"
        if atype == "Stock":
            try:
                report = diagnose_stock(meta["ts_code"])
                score = report["overall_score"]
                advice = report.get("advice") or build_trade_advice(
                    close=ind.get("close", 0),
                    total_score=score,
                    volatility=ind.get("volatility", 20),
                    rsi=ind.get("rsi14", 50),
                    ret_20=ind.get("ret_20", 0),
                )
                level = report["overall_level"]
            except Exception:  # noqa: BLE001
                score = 55.0
                level = "一般"
                advice = build_trade_advice(
                    close=ind.get("close", 0),
                    total_score=score,
                    volatility=ind.get("volatility", 20),
                    rsi=ind.get("rsi14", 50),
                    ret_20=ind.get("ret_20", 0),
                    asset_type="Stock",
                )
        else:
            score = float(min(95, max(35, 60 + ind.get("ret_20", 0))))
            level = "良好" if score >= 65 else "一般"
            advice = build_trade_advice(
                close=ind.get("close", 0),
                total_score=score,
                volatility=ind.get("volatility", 15),
                rsi=ind.get("rsi14", 50),
                ret_20=ind.get("ret_20", 0),
                asset_type=atype,
            )

        cost = h.get("cost")
        pnl = None
        if cost:
            pnl = round((ind.get("close", 0) / float(cost) - 1) * 100, 2)
        score_acc += score * w
        details.append(
            {
                "ts_code": meta["ts_code"],
                "name": meta["name"],
                "asset_type": meta.get("asset_type", "Stock"),
                "weight": round(w * 100, 2),
                "close": ind.get("close"),
                "pct_chg": ind.get("pct_chg"),
                "score": round(score, 1),
                "level": level,
                "pnl_pct": pnl,
                "advice": advice,
            }
        )

    # 简易分散度
    conc = max(d["weight"] for d in details) if details else 0
    suggestions = []
    if conc > 40:
        suggestions.append("单一持仓过高，建议再平衡，单票权重控制在 25% 以内。")
    if score_acc < 55:
        suggestions.append("组合综合评分偏低，优先削减弱项或替换为更高评分资产。")
    else:
        suggestions.append("组合评分尚可，按各标的止损止盈纪律滚动管理。")
    suggestions.append("小资金建议：核心宽基 ETF + 少量高分个股/主题，固收底仓降波动。")

    return {
        "trade_date": date.today(),
        "portfolio_score": round(score_acc, 1),
        "concentration_top": round(conc, 1),
        "holdings": details,
        "suggestions": suggestions,
        "allocation_hint": {
            "stock": "30%-50%",
            "etf": "30%-50%",
            "bond_or_cash": "20%-40%",
            "note": "按风险承受能力调整，新手优先 ETF/债券底仓。",
        },
    }