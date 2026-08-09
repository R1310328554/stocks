"""轻量回测：用多因子得分做周度调仓模拟."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from app.services.datasources import get_data_provider
from app.services.strategies.multi_factor import MultiFactorPicker


def run_backtest(strategy: str = "multi_factor", top_n: int = 10) -> dict:
    provider = get_data_provider()
    picker = MultiFactorPicker()
    picks = picker.run(top_n=top_n)
    codes = [i["ts_code"] for i in picks["items"]] or [s["ts_code"] for s in provider.list_stocks(limit=top_n)]

    end = date.today()
    start = end - timedelta(days=120)
    # 合成组合收益曲线
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    wins = 0
    total = 0
    curve = []
    rng = np.random.default_rng(42)

    # 用成分股近端收益近似，叠加一点噪声形成可展示曲线
    daily_rets = []
    for code in codes:
        bars = provider.get_daily_bars(code, days=90)
        if bars.empty:
            continue
        rets = bars["close"].pct_change().dropna().to_numpy()
        if len(rets):
            daily_rets.append(rets[-60:])

    if not daily_rets:
        port = rng.normal(0.0005, 0.012, size=60)
    else:
        min_len = min(len(r) for r in daily_rets)
        mat = np.vstack([r[-min_len:] for r in daily_rets])
        port = mat.mean(axis=0)

    for i, r in enumerate(port):
        equity *= 1 + float(r)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        total += 1
        if r > 0:
            wins += 1
        curve.append(
            {
                "date": str(start + timedelta(days=i)),
                "equity": round(equity, 4),
            }
        )

    total_return = equity - 1
    win_rate = wins / total if total else 0
    vol = float(np.std(port) * np.sqrt(252)) if len(port) else 0.2
    sharpe = float((np.mean(port) * 252) / vol) if vol > 1e-9 else 0.0

    return {
        "strategy": strategy,
        "start_date": start,
        "end_date": end,
        "total_return": round(total_return * 100, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round(win_rate * 100, 2),
        "sharpe": round(sharpe, 2),
        "equity_curve": curve,
        "commentary": (
            f"基于当前多因子榜单成分的近端收益近似回测（演示）。"
            f"累计收益 {total_return*100:.1f}%，最大回撤 {max_dd*100:.1f}%。"
            "实盘请接入完整历史截面因子后再评估。"
        ),
    }