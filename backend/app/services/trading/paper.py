"""模拟交易账户：初始 10 万，从订单流水推导持仓与盈亏。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import PaperOrder
from app.services.datasources import get_data_provider
from app.services.realtime import quote_snapshot

INITIAL_CASH = 100_000.0


async def place_order(db: AsyncSession, ts_code: str, side: str, shares: int) -> dict:
    provider = get_data_provider()
    meta = provider.resolve_name(ts_code)
    snap = quote_snapshot(codes=[meta["ts_code"]], limit=1)
    if not snap["items"]:
        raise ValueError("无法获取行情")
    price = snap["items"][0]["price"]
    shares = int(shares)
    if shares <= 0 or shares % 100 != 0:
        raise ValueError("股数需为100的整数倍")
    amount = round(price * shares, 2)

    state = await account_state(db)
    if side == "buy" and amount > state["cash"]:
        raise ValueError(f"现金不足：需要 {amount}，可用 {state['cash']}")
    if side == "sell":
        pos = next((p for p in state["positions"] if p["ts_code"] == meta["ts_code"]), None)
        if not pos or pos["shares"] < shares:
            raise ValueError("持仓不足")

    order = PaperOrder(
        ts_code=meta["ts_code"],
        name=meta["name"],
        side=side,
        price=price,
        shares=shares,
        amount=amount,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {
        "id": order.id,
        "ts_code": order.ts_code,
        "name": order.name,
        "side": side,
        "price": price,
        "shares": shares,
        "amount": amount,
    }


async def account_state(db: AsyncSession) -> dict:
    result = await db.execute(select(PaperOrder).order_by(PaperOrder.created_at))
    orders = list(result.scalars().all())

    cash = INITIAL_CASH
    lots: dict[str, dict] = {}
    for o in orders:
        if o.side == "buy":
            cash -= o.amount
            lot = lots.setdefault(o.ts_code, {"name": o.name, "shares": 0, "cost": 0.0})
            lot["cost"] += o.amount
            lot["shares"] += o.shares
        else:
            cash += o.amount
            lot = lots.setdefault(o.ts_code, {"name": o.name, "shares": 0, "cost": 0.0})
            if lot["shares"] > 0:
                avg = lot["cost"] / lot["shares"]
                lot["cost"] -= avg * o.shares
            lot["shares"] -= o.shares

    codes = [c for c, l in lots.items() if l["shares"] > 0]
    quotes = {q["ts_code"]: q for q in quote_snapshot(codes=codes, limit=50)["items"]} if codes else {}

    positions = []
    market_value = 0.0
    for code, lot in lots.items():
        if lot["shares"] <= 0:
            continue
        q = quotes.get(code)
        price = q["price"] if q else 0.0
        mv = round(price * lot["shares"], 2)
        avg_cost = lot["cost"] / lot["shares"] if lot["shares"] else 0
        pnl = round(mv - lot["cost"], 2)
        market_value += mv
        positions.append(
            {
                "ts_code": code,
                "name": lot["name"],
                "shares": lot["shares"],
                "avg_cost": round(avg_cost, 3),
                "price": price,
                "market_value": mv,
                "pnl": pnl,
                "pnl_pct": round(pnl / lot["cost"] * 100, 2) if lot["cost"] else 0,
            }
        )

    total = round(cash + market_value, 2)
    return {
        "initial_cash": INITIAL_CASH,
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "total_assets": total,
        "total_pnl": round(total - INITIAL_CASH, 2),
        "total_pnl_pct": round((total - INITIAL_CASH) / INITIAL_CASH * 100, 2),
        "positions": positions,
        "orders": [
            {
                "id": o.id,
                "ts_code": o.ts_code,
                "name": o.name,
                "side": o.side,
                "price": o.price,
                "shares": o.shares,
                "amount": o.amount,
                "created_at": o.created_at.isoformat() + "Z",
            }
            for o in reversed(orders[-30:])
        ],
    }


async def reset_account(db: AsyncSession) -> dict:
    result = await db.execute(select(PaperOrder))
    for o in result.scalars().all():
        await db.delete(o)
    await db.commit()
    return {"ok": True, "cash": INITIAL_CASH}