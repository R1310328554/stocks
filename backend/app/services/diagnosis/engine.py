"""智能诊股：基本面 / 技术面 / 资金面 / 风险提示."""

from __future__ import annotations

from datetime import date

from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators, detect_patterns
from app.services.sentiment.capital_flow import analyze_capital_flow


def _level(score: float) -> str:
    if score >= 80:
        return "优秀"
    if score >= 65:
        return "良好"
    if score >= 50:
        return "一般"
    if score >= 35:
        return "偏弱"
    return "较差"


def diagnose_stock(ts_code: str) -> dict:
    provider = get_data_provider()
    stock = provider.resolve_name(ts_code)
    bars = provider.get_daily_bars(stock["ts_code"], days=180)
    fund = provider.get_fundamentals(stock["ts_code"])
    ind = compute_indicators(bars)
    patterns = detect_patterns(bars)
    capital = analyze_capital_flow(stock["ts_code"])

    # 基本面评分
    f_score = 50.0
    f_details: list[str] = []
    if fund["roe"] >= 15:
        f_score += 12
        f_details.append(f"ROE {fund['roe']}% 表现优秀")
    elif fund["roe"] >= 8:
        f_score += 5
        f_details.append(f"ROE {fund['roe']}% 尚可")
    else:
        f_score -= 8
        f_details.append(f"ROE {fund['roe']}% 偏弱")

    if 0 < fund["pe"] <= 25:
        f_score += 10
        f_details.append(f"PE {fund['pe']} 估值相对合理")
    elif fund["pe"] > 60:
        f_score -= 10
        f_details.append(f"PE {fund['pe']} 估值偏高")
    else:
        f_details.append(f"PE {fund['pe']}")

    if fund["profit_growth"] >= 20:
        f_score += 10
        f_details.append(f"净利增长 {fund['profit_growth']}%")
    elif fund["profit_growth"] < 0:
        f_score -= 10
        f_details.append(f"净利增长 {fund['profit_growth']}% 承压")

    if fund["debt_ratio"] > 70:
        f_score -= 8
        f_details.append(f"资产负债率 {fund['debt_ratio']}% 偏高")
    else:
        f_score += 4
        f_details.append(f"资产负债率 {fund['debt_ratio']}% 可控")

    f_score = max(0, min(100, f_score))

    # 技术面
    t_score = 50.0
    t_details: list[str] = []
    if ind.get("ma5", 0) > ind.get("ma20", 0) > ind.get("ma60", 0):
        t_score += 15
        t_details.append("均线多头排列")
    elif ind.get("ma5", 0) < ind.get("ma20", 0) < ind.get("ma60", 0):
        t_score -= 12
        t_details.append("均线空头排列")
    else:
        t_details.append("均线纠结，方向待明")

    rsi = ind.get("rsi14", 50)
    if 45 <= rsi <= 65:
        t_score += 8
        t_details.append(f"RSI {rsi} 处于健康区间")
    elif rsi > 75:
        t_score -= 10
        t_details.append(f"RSI {rsi} 超买")
    elif rsi < 30:
        t_score += 5
        t_details.append(f"RSI {rsi} 超卖，关注反弹")

    if ind.get("macd", 0) > 0:
        t_score += 6
        t_details.append("MACD 位于零轴上方")
    else:
        t_score -= 4
        t_details.append("MACD 位于零轴下方")

    if patterns:
        t_score += 6
        t_details.append("形态：" + "、".join(patterns))
    t_score = max(0, min(100, t_score))

    # 资金面
    c_score = 50.0
    c_details = [capital["summary"]]
    if "看多" in capital["consensus"]:
        c_score += 18
    elif "看空" in capital["consensus"]:
        c_score -= 15
    elif "背离" in capital["consensus"]:
        c_score -= 5
    if capital["crowding_percentile"] >= 90:
        c_score -= 10
        c_details.append("资金拥挤度偏高")
    c_score = max(0, min(100, c_score))

    risks: list[str] = []
    if fund["debt_ratio"] > 70:
        risks.append("财务杠杆偏高，关注偿债压力")
    if fund["pe"] > 70:
        risks.append("估值泡沫风险")
    if fund["profit_growth"] < -10:
        risks.append("盈利下滑风险")
    if capital["crowding_percentile"] >= 90:
        risks.append("短线资金拥挤，波动放大")
    if ind.get("volatility", 0) > 45:
        risks.append("波动率偏高，仓位需克制")
    if not risks:
        risks.append("暂无明显硬性风险信号，仍需结合仓位与宏观环境")

    overall = round(f_score * 0.35 + t_score * 0.35 + c_score * 0.3, 1)
    signals = list(ind.get("signals", [])) + patterns

    return {
        "ts_code": stock["ts_code"],
        "name": stock["name"],
        "industry": stock.get("industry", ""),
        "trade_date": date.today(),
        "overall_score": overall,
        "overall_level": _level(overall),
        "fundamental": {
            "score": round(f_score, 1),
            "level": _level(f_score),
            "summary": "财务健康度与估值成长综合评估",
            "details": f_details,
        },
        "technical": {
            "score": round(t_score, 1),
            "level": _level(t_score),
            "summary": "趋势、动量与形态综合判断",
            "details": t_details,
        },
        "capital": {
            "score": round(c_score, 1),
            "level": _level(c_score),
            "summary": "主力/北向/大宗资金合力判断",
            "details": c_details,
        },
        "risks": risks,
        "signals": signals,
        "indicators": {
            k: v
            for k, v in ind.items()
            if k != "series"
        } | {"series": ind.get("series", {}), "fundamentals": fund},
    }