"""实时行情快照与推送（演示流；live 可替换为 WebSocket 行情商）。"""

from __future__ import annotations

import asyncio
from datetime import datetime

import numpy as np

from app.services.datasources import get_data_provider
from app.services.datasources.multi_asset import list_assets


def quote_snapshot(codes: list[str] | None = None, limit: int = 30) -> dict:
    provider = get_data_provider()
    if not codes:
        codes = [a["ts_code"] for a in list_assets("stock")[:limit]]
    items = []
    now = datetime.utcnow().isoformat() + "Z"
    for code in codes:
        meta = provider.resolve_name(code)
        bars = provider.get_daily_bars(code if "." in code else meta["ts_code"], days=5)
        if bars.empty:
            continue
        last = bars.iloc[-1]
        rng = np.random.default_rng(abs(hash(code + now[:16])) % (2**32))
        jitter = float(rng.normal(0, 0.15))
        price = float(last["close"]) * (1 + jitter / 100)
        items.append(
            {
                "ts_code": meta["ts_code"],
                "name": meta["name"],
                "price": round(price, 3),
                "pct_chg": round(float(last["pct_chg"]) + jitter, 2),
                "volume": float(last["vol"]),
                "amount": float(last["amount"]),
                "bid": round(price * 0.999, 3),
                "ask": round(price * 1.001, 3),
                "updated_at": now,
                "source": provider.source_name,
            }
        )
    return {"server_time": now, "mode": "realtime_sim", "items": items}


async def stream_ticks(codes: list[str] | None = None):
    while True:
        yield quote_snapshot(codes=codes, limit=20)
        await asyncio.sleep(2)