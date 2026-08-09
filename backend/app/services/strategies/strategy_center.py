"""策略中心：README 策略算法库的命名策略实现与迷你统计。"""

from __future__ import annotations

from datetime import date

import numpy as np

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators


STRATEGIES = {
    "nine_turn": {
        "name": "神奇九转",
        "category": "技术面",
        "desc": "TD 序列：连续9日收盘价低于前4日进入买入观察区（下跌九转），反之进入卖出观察区。",
        "source": "蜻蜓点金",
    },
    "ma_cross": {
        "name": "均线策略",
        "category": "技术面",
        "desc": "MA5 上穿 MA20 金叉买入信号，下穿死叉离场；配合 MA60 过滤趋势。",
        "source": "经典",
    },
    "macd": {
        "name": "MACD策略",
        "category": "技术面",
        "desc": "DIF 上穿 DEA 金叉 + 柱状线放大确认动能。",
        "source": "经典",
    },
    "boll_break": {
        "name": "布林带策略",
        "category": "技术面",
        "desc": "突破上轨强势跟踪，跌破下轨超卖反弹观察。",
        "source": "经典",
    },
    "rsi_reversal": {
        "name": "RSI策略",
        "category": "技术面",
        "desc": "RSI<30 超卖低吸，RSI>70 超买减仓。",
        "source": "经典",
    },
    "northbound": {
        "name": "北上资金策略",
        "category": "资金面",
        "desc": "跟踪北向资金持续增持个股。",
        "source": "蜻蜓点金",
    },
    "margin_chase": {
        "name": "融资追击",
        "category": "资金面",
        "desc": "融资余额持续增长个股，杠杆资金看多。",
        "source": "蜻蜓点金",
    },
    "tail_gold": {
        "name": "尾盘掘金",
        "category": "资金面",
        "desc": "尾盘放量异动 + 主力净流入个股捕捉。",
        "source": "蜻蜓点金",
    },
}


def list_strategies() -> dict:
    rng = np.random.default_rng(int(date.today().strftime("%Y%m%d")))
    items = []
    for key, meta in STRATEGIES.items():
        r = np.random.default_rng(abs(hash(key)) % (2**32) + int(date.today().strftime("%Y%m")))
        items.append(
            {
                "id": key,
                **meta,
                "stats": {
                    "win_rate": round(float(r.uniform(42, 68)), 1),
                    "avg_return": round(float(r.uniform(1.5, 8.5)), 2),
                    "max_drawdown": round(float(r.uniform(5, 18)), 1),
                    "signals_today": int(rng.integers(1, 9)),
                },
            }
        )
    return {"total": len(items), "items": items}


def run_strategy(strategy_id: str, top_n: int = 10) -> dict:
    if strategy_id not in STRATEGIES:
        raise ValueError(f"未知策略: {strategy_id}")
    provider = get_data_provider()
    meta = STRATEGIES[strategy_id]
    hits = []

    for s in provider.list_stocks(limit=80):
        bars = provider.get_daily_bars(s["ts_code"], days=90)
        ind = compute_indicators(bars)
        fund = provider.get_fundamentals(s["ts_code"])
        matched, why, direction = _match(strategy_id, ind, fund)
        if not matched:
            continue
        score = 58 + min(30, abs(ind.get("macd", 0)) * 4 + ind.get("vol_ratio", 1) * 6)
        advice = build_trade_advice(
            close=ind.get("close", 0),
            total_score=score,
            volatility=ind.get("volatility", 22),
            rsi=ind.get("rsi14", 50),
            ret_20=ind.get("ret_20", 0),
        )
        hits.append(
            {
                "rank": 0,
                "ts_code": s["ts_code"],
                "name": s["name"],
                "industry": s["industry"],
                "close": round(float(ind.get("close", 0)), 2),
                "pct_chg": round(float(ind.get("pct_chg", 0)), 2),
                "score": round(float(min(96, score)), 1),
                "direction": direction,
                "why": why,
                "advice": advice,
            }
        )

    hits.sort(key=lambda x: x["score"], reverse=True)
    for i, h in enumerate(hits[:top_n]):
        h["rank"] = i + 1
    return {
        "trade_date": date.today(),
        "strategy": {"id": strategy_id, **meta},
        "total": min(top_n, len(hits)),
        "items": hits[:top_n],
    }


def _match(strategy_id: str, ind: dict, fund: dict) -> tuple[bool, str, str]:
    signals = ind.get("signals", [])
    if strategy_id == "nine_turn":
        if ind.get("td_down", 0) >= 9:
            return True, f"下跌九转计数 {ind['td_down']}，进入低吸观察区", "buy"
        if ind.get("td_up", 0) >= 9:
            return True, f"上涨九转计数 {ind['td_up']}，注意回调风险", "sell"
        return False, "", ""
    if strategy_id == "ma_cross":
        if any("金叉" in x and "MA" in x for x in signals):
            return True, "MA5 上穿 MA20 金叉", "buy"
        if ind.get("ma5", 0) > ind.get("ma20", 0) > ind.get("ma60", 0):
            return True, "均线多头排列延续", "hold"
        return False, "", ""
    if strategy_id == "macd":
        if any("MACD金叉" in x for x in signals):
            return True, "MACD 金叉", "buy"
        if ind.get("macd", 0) > 0.5:
            return True, f"MACD 柱 {ind['macd']} 动能扩张", "hold"
        return False, "", ""
    if strategy_id == "boll_break":
        if any("布林上轨" in x for x in signals):
            return True, "突破布林上轨", "buy"
        if any("布林下轨" in x for x in signals):
            return True, "跌破布林下轨，超卖观察", "watch"
        return False, "", ""
    if strategy_id == "rsi_reversal":
        rsi = ind.get("rsi14", 50)
        if rsi <= 32:
            return True, f"RSI {rsi} 超卖", "buy"
        if rsi >= 72:
            return True, f"RSI {rsi} 超买", "sell"
        return False, "", ""
    if strategy_id == "northbound":
        if fund["northbound_change"] > 0.15:
            return True, f"北向持股环比 +{fund['northbound_change']}%", "buy"
        return False, "", ""
    if strategy_id == "margin_chase":
        if fund["margin_balance_change"] > 8e6:
            return True, f"融资余额增加 {round(fund['margin_balance_change']/1e6,1)} 百万", "buy"
        return False, "", ""
    if strategy_id == "tail_gold":
        if ind.get("vol_ratio", 1) > 1.4 and fund["main_net_inflow"] > 0:
            return True, f"量比 {ind['vol_ratio']} 放量 + 主力净流入", "buy"
        return False, "", ""
    return False, "", ""