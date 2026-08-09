"""交易建议：持有周期、止损、止盈、仓位建议。"""

from __future__ import annotations

from typing import Any


def build_trade_advice(
    *,
    close: float,
    total_score: float,
    volatility: float,
    rsi: float,
    ret_20: float,
    asset_type: str = "Stock",
    factors: dict[str, float] | None = None,
) -> dict[str, Any]:
    factors = factors or {}
    # 评分档位
    if total_score >= 75:
        action = "积极关注/分批建仓"
        confidence = "高"
        hold_days = (20, 60)
        position = "建议仓位 10%-20%"
    elif total_score >= 60:
        action = "可关注/轻仓试探"
        confidence = "中"
        hold_days = (10, 30)
        position = "建议仓位 5%-12%"
    elif total_score >= 45:
        action = "观望为主"
        confidence = "中低"
        hold_days = (5, 15)
        position = "建议仓位不超过 5%"
    else:
        action = "暂不建议介入"
        confidence = "低"
        hold_days = (0, 0)
        position = "建议空仓或仅观察"

    # 波动率自适应止损止盈
    vol = max(volatility, 12.0)
    if asset_type == "Bond":
        stop_pct = min(3.0, max(1.0, vol * 0.08))
        take_pct = min(6.0, max(2.0, vol * 0.15))
        hold_label = "中长持有（利率/信用策略）"
        hold_days = (60, 180)
        position = "固收仓位按风险预算配置，单券建议 ≤15%"
    elif asset_type in {"ETF", "LOF", "Fund"}:
        stop_pct = min(10.0, max(4.0, vol * 0.35))
        take_pct = min(18.0, max(7.0, vol * 0.7))
        hold_label = "波段/定投均可，偏中期"
        hold_days = (20, 90)
    else:
        stop_pct = min(12.0, max(5.0, vol * 0.45))
        take_pct = min(25.0, max(8.0, vol * 0.9))
        # 动量强则缩短持有、提高止盈灵敏度
        if factors.get("momentum", 50) > 70 and ret_20 > 8:
            hold_days = (5, 20)
            hold_label = "短线波段（动量偏强）"
            take_pct *= 0.85
        elif factors.get("quality", 50) > 70 and factors.get("value", 50) > 60:
            hold_days = (30, 90)
            hold_label = "中长线持有（质地偏优）"
        else:
            hold_label = "中短线观察持有"

    # RSI 微调
    if rsi >= 75:
        action = "谨慎追高，等待回调再评估"
        stop_pct *= 0.85
    elif rsi <= 30 and total_score >= 55:
        action = "超卖区可分批低吸"
        take_pct *= 1.05

    if close <= 0:
        close = 1.0
    stop_price = round(close * (1 - stop_pct / 100), 3)
    take_price = round(close * (1 + take_pct / 100), 3)
    trail_pct = round(max(3.0, stop_pct * 0.7), 2)

    checklist = [
        f"入场参考价附近：{close}",
        f"跌破止损价 {stop_price}（-{stop_pct:.1f}%）执行止损",
        f"触及止盈价 {take_price}（+{take_pct:.1f}%）分批止盈",
        f"移动止盈回撤阈值约 {trail_pct}%",
        position,
    ]
    if hold_days[1] > 0:
        checklist.append(f"计划持有 {hold_days[0]}-{hold_days[1]} 个交易日，到期复盘")

    return {
        "action": action,
        "confidence": confidence,
        "hold_horizon": hold_label,
        "hold_days_min": hold_days[0],
        "hold_days_max": hold_days[1],
        "position_advice": position,
        "entry_price": round(close, 3),
        "stop_loss_pct": round(stop_pct, 2),
        "take_profit_pct": round(take_pct, 2),
        "stop_loss_price": stop_price,
        "take_profit_price": take_price,
        "trailing_stop_pct": trail_pct,
        "checklist": checklist,
        "risk_note": "建议仅作研究辅助，不构成投资承诺；小资金优先分散与严格止损。",
    }