"""多因子选股引擎：价值/成长/质量/动量/资金/情绪."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators, detect_patterns


WEIGHTS = {
    "value": 0.18,
    "growth": 0.18,
    "quality": 0.18,
    "momentum": 0.18,
    "capital": 0.15,
    "sentiment": 0.13,
}


@dataclass
class ScoredStock:
    ts_code: str
    name: str
    industry: str
    total_score: float
    factors: dict[str, float]
    reason: str
    close: float
    pct_chg: float
    pe: float
    pb: float
    roe: float
    meta: dict


def _percentile_score(series: pd.Series, higher_better: bool = True) -> pd.Series:
    ranks = series.rank(pct=True, method="average")
    if not higher_better:
        ranks = 1 - ranks
    return (ranks * 100).fillna(50)


class MultiFactorPicker:
    def __init__(self) -> None:
        self.provider = get_data_provider()
        self.settings = get_settings()

    def run(
        self,
        top_n: int | None = None,
        industries: list[str] | None = None,
        max_pe: float | None = None,
        min_roe: float | None = None,
        min_profit_growth: float | None = None,
        require_patterns: list[str] | None = None,
        market: str | None = None,
    ) -> dict:
        top_n = top_n or self.settings.top_n_picks
        universe = self.provider.list_stocks(limit=self.settings.default_universe_size)
        rows: list[dict] = []

        for stock in universe:
            if industries and stock["industry"] not in industries:
                continue
            if market and market not in (stock.get("market") or ""):
                continue

            bars = self.provider.get_daily_bars(stock["ts_code"], days=self.settings.factor_lookback_days)
            fund = self.provider.get_fundamentals(stock["ts_code"])
            ind = compute_indicators(bars)
            patterns = detect_patterns(bars)
            if require_patterns and not any(p in patterns for p in require_patterns):
                continue
            if max_pe is not None and fund["pe"] > max_pe:
                continue
            if min_roe is not None and fund["roe"] < min_roe:
                continue
            if min_profit_growth is not None and fund["profit_growth"] < min_profit_growth:
                continue

            rows.append(
                {
                    **stock,
                    **fund,
                    "close": ind.get("close", 0.0),
                    "pct_chg": ind.get("pct_chg", 0.0),
                    "ret_20": ind.get("ret_20", 0.0),
                    "ret_60": ind.get("ret_60", 0.0),
                    "rsi14": ind.get("rsi14", 50.0),
                    "macd": ind.get("macd", 0.0),
                    "vol_ratio": ind.get("vol_ratio", 1.0),
                    "volatility": ind.get("volatility", 20.0),
                    "patterns": patterns,
                    "tech_signals": ind.get("signals", []),
                }
            )

        if not rows:
            return {
                "trade_date": date.today(),
                "strategy": "multi_factor",
                "data_source": self.provider.source_name,
                "total": 0,
                "items": [],
            }

        df = pd.DataFrame(rows)
        value = (
            _percentile_score(1 / df["pe"].clip(lower=1), True) * 0.35
            + _percentile_score(1 / df["pb"].clip(lower=0.2), True) * 0.25
            + _percentile_score(1 / df["ps"].clip(lower=0.2), True) * 0.2
            + _percentile_score(df["dividend_yield"], True) * 0.2
        )
        growth = (
            _percentile_score(df["revenue_growth"], True) * 0.35
            + _percentile_score(df["profit_growth"], True) * 0.4
            + _percentile_score(df["eps_growth"], True) * 0.25
        )
        quality = (
            _percentile_score(df["roe"], True) * 0.35
            + _percentile_score(df["roa"], True) * 0.2
            + _percentile_score(df["gross_margin"], True) * 0.2
            + _percentile_score(df["net_margin"], True) * 0.15
            + _percentile_score(df["debt_ratio"], False) * 0.1
        )
        # 动量：适度上涨加分，极端超买扣分
        momentum_raw = (
            _percentile_score(df["ret_20"], True) * 0.4
            + _percentile_score(df["ret_60"], True) * 0.3
            + _percentile_score(df["macd"], True) * 0.2
            + _percentile_score((70 - (df["rsi14"] - 50).abs()), True) * 0.1
        )
        capital = (
            _percentile_score(df["main_net_inflow"], True) * 0.45
            + _percentile_score(df["northbound_change"], True) * 0.35
            + _percentile_score(df["margin_balance_change"], True) * 0.2
        )
        sentiment = (
            _percentile_score(df["turnover"], True) * 0.35
            + _percentile_score(df["vol_ratio"], True) * 0.35
            + _percentile_score(df["volatility"], False) * 0.3
        )

        df["value_score"] = value
        df["growth_score"] = growth
        df["quality_score"] = quality
        df["momentum_score"] = momentum_raw
        df["capital_score"] = capital
        df["sentiment_score"] = sentiment
        df["total_score"] = (
            value * WEIGHTS["value"]
            + growth * WEIGHTS["growth"]
            + quality * WEIGHTS["quality"]
            + momentum_raw * WEIGHTS["momentum"]
            + capital * WEIGHTS["capital"]
            + sentiment * WEIGHTS["sentiment"]
        )

        df = df.sort_values("total_score", ascending=False).head(top_n).reset_index(drop=True)
        items = []
        for i, row in df.iterrows():
            reason = self._build_reason(row)
            items.append(
                {
                    "rank": int(i) + 1,
                    "ts_code": row["ts_code"],
                    "name": row["name"],
                    "industry": row["industry"],
                    "total_score": round(float(row["total_score"]), 2),
                    "factors": {
                        "value": round(float(row["value_score"]), 2),
                        "growth": round(float(row["growth_score"]), 2),
                        "quality": round(float(row["quality_score"]), 2),
                        "momentum": round(float(row["momentum_score"]), 2),
                        "capital": round(float(row["capital_score"]), 2),
                        "sentiment": round(float(row["sentiment_score"]), 2),
                    },
                    "reason": reason,
                    "close": round(float(row["close"]), 2),
                    "pct_chg": round(float(row["pct_chg"]), 2),
                    "pe": round(float(row["pe"]), 2),
                    "pb": round(float(row["pb"]), 2),
                    "roe": round(float(row["roe"]), 2),
                }
            )

        return {
            "trade_date": date.today(),
            "strategy": "multi_factor",
            "data_source": self.provider.source_name,
            "total": len(items),
            "items": items,
        }

    def _build_reason(self, row: pd.Series) -> str:
        parts: list[str] = []
        scores = {
            "价值": row["value_score"],
            "成长": row["growth_score"],
            "质量": row["quality_score"],
            "动量": row["momentum_score"],
            "资金": row["capital_score"],
            "情绪": row["sentiment_score"],
        }
        top_factors = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
        parts.append("、".join(f"{k}因子靠前" for k, _ in top_factors))
        if row["roe"] >= 15:
            parts.append(f"ROE {row['roe']:.1f}%")
        if row["profit_growth"] >= 20:
            parts.append(f"净利增长 {row['profit_growth']:.1f}%")
        if row["main_net_inflow"] > 0:
            parts.append("主力净流入")
        if row["northbound_change"] > 0:
            parts.append("北向增持")
        patterns = row.get("patterns") or []
        if patterns:
            parts.append("/".join(patterns[:2]))
        return "；".join(parts)