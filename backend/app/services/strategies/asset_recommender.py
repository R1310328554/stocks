"""基金 / ETF / LOF / 债券 多维推荐引擎。"""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.services.advice.trade_plan import build_trade_advice
from app.services.datasources import get_data_provider
from app.services.datasources.multi_asset import asset_metrics, list_assets
from app.services.indicators.technical import compute_indicators


def _pct_rank(series: pd.Series, higher_better: bool = True) -> pd.Series:
    ranks = series.rank(pct=True)
    if not higher_better:
        ranks = 1 - ranks
    return (ranks * 100).fillna(50)


class AssetRecommender:
    def __init__(self) -> None:
        self.provider = get_data_provider()

    def recommend(self, asset_type: str, top_n: int = 10, style: str | None = None) -> dict:
        asset_type = asset_type.lower()
        type_map = {"etf": "ETF", "lof": "LOF", "fund": "Fund", "bond": "Bond"}
        label = type_map.get(asset_type, asset_type.upper())
        universe = list_assets(asset_type)
        if style:
            universe = [u for u in universe if style in (u.get("industry") or "")]

        rows: list[dict] = []
        for item in universe:
            m = asset_metrics(item["ts_code"], label)
            bars = self.provider.get_daily_bars(item["ts_code"], days=90)
            ind = compute_indicators(bars)
            rows.append({**item, **m, "rsi": ind.get("rsi14", 50), "macd": ind.get("macd", 0)})

        if not rows:
            return {
                "trade_date": date.today(),
                "asset_type": label,
                "strategy": f"{asset_type}_recommend",
                "data_source": self.provider.source_name,
                "total": 0,
                "items": [],
            }

        df = pd.DataFrame(rows)
        if label == "Bond":
            score = (
                _pct_rank(df["ytm"]) * 0.35
                + _pct_rank(df["credit_rating"].map({"AAA": 3, "AA+": 2.5, "AA": 2, "AA-": 1.5})) * 0.25
                + _pct_rank(df["duration"], False) * 0.15
                + _pct_rank(df["liquidity_score"]) * 0.15
                + _pct_rank(df["spread_bp"], False) * 0.1
            )
        else:
            score = (
                _pct_rank(df["ytd_return"]) * 0.22
                + _pct_rank(df["sharpe"]) * 0.22
                + _pct_rank(df["max_drawdown"], False) * 0.18
                + _pct_rank(df["manager_score"]) * 0.15
                + _pct_rank(df["expense_ratio"], False) * 0.1
                + _pct_rank(df["liquidity_score"]) * 0.08
                + _pct_rank(df["tracking_error"], False) * 0.05
            )

        df["total_score"] = score
        df = df.sort_values("total_score", ascending=False).head(top_n).reset_index(drop=True)

        items = []
        for i, row in df.iterrows():
            factors = {
                "value": round(float(100 - row.get("expense_ratio", 0.5) * 30), 2)
                if label != "Bond"
                else round(float(row.get("ytm", 2) * 20), 2),
                "growth": round(float(row.get("ytd_return", row.get("ret_60", 0)) + 50), 2),
                "quality": round(float(row.get("manager_score", row.get("liquidity_score", 60))), 2),
                "momentum": round(float(50 + row.get("ret_20", 0)), 2),
                "capital": round(float(row.get("liquidity_score", 60)), 2),
                "sentiment": round(float(100 - abs(row.get("rsi", 50) - 50)), 2),
            }
            advice = build_trade_advice(
                close=float(row["close"]),
                total_score=float(row["total_score"]),
                volatility=float(row.get("volatility", 15)),
                rsi=float(row.get("rsi", 50)),
                ret_20=float(row.get("ret_20", 0)),
                asset_type=label,
                factors=factors,
            )
            reason_bits = []
            if label == "Bond":
                reason_bits.append(f"YTM {row['ytm']}%")
                reason_bits.append(f"久期 {row['duration']}")
                reason_bits.append(f"评级 {row['credit_rating']}")
            else:
                reason_bits.append(f"YTD {row['ytd_return']}%")
                reason_bits.append(f"夏普 {row['sharpe']}")
                reason_bits.append(f"最大回撤 {row['max_drawdown']}%")
                if "premium" in row:
                    reason_bits.append(f"溢价 {row['premium']}%")

            items.append(
                {
                    "rank": int(i) + 1,
                    "ts_code": row["ts_code"],
                    "name": row["name"],
                    "industry": row["industry"],
                    "asset_type": label,
                    "manager": row.get("manager", ""),
                    "total_score": round(float(row["total_score"]), 2),
                    "factors": factors,
                    "reason": "；".join(reason_bits),
                    "close": round(float(row["close"]), 3),
                    "pct_chg": round(float(row["pct_chg"]), 2),
                    "metrics": {
                        k: (round(float(row[k]), 3) if isinstance(row[k], (int, float)) else row[k])
                        for k in row.index
                        if k
                        in {
                            "nav",
                            "premium",
                            "tracking_error",
                            "expense_ratio",
                            "sharpe",
                            "max_drawdown",
                            "ytd_return",
                            "ytm",
                            "duration",
                            "credit_rating",
                            "spread_bp",
                            "coupon",
                            "liquidity_score",
                        }
                        and k in row
                    },
                    "advice": advice,
                }
            )

        return {
            "trade_date": date.today(),
            "asset_type": label,
            "strategy": f"{asset_type}_multi_factor",
            "data_source": self.provider.source_name,
            "total": len(items),
            "items": items,
            "methodology": self._methodology(label),
        }

    def _methodology(self, label: str) -> str:
        if label == "Bond":
            return "债券评分：收益率(YTM) + 信用评级 + 久期风险 + 流动性 + 信用利差（参考中债估值逻辑）。"
        return "基金/ETF/LOF 评分：收益 + 夏普 + 回撤控制 + 管理人/质量 + 费率 + 流动性/跟踪误差。"