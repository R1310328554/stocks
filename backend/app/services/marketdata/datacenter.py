"""数据中心服务（demo 数据与 live 同构，可替换为交易所/东财/巨潮源）。"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np

from app.services.datasources import get_data_provider
from app.services.indicators.technical import compute_indicators


def _rows_with_indicators(limit: int = 60) -> list[dict]:
    provider = get_data_provider()
    rows = []
    for s in provider.list_stocks(limit=limit):
        bars = provider.get_daily_bars(s["ts_code"], days=40)
        ind = compute_indicators(bars)
        fund = provider.get_fundamentals(s["ts_code"])
        rows.append(
            {
                **s,
                "close": ind.get("close", 0),
                "pct_chg": ind.get("pct_chg", 0),
                "ret_5": ind.get("ret_5", 0),
                "vol_ratio": ind.get("vol_ratio", 1),
                "turnover": fund["turnover"],
                "main_net_inflow": fund["main_net_inflow"],
                "amount": float(bars["amount"].iloc[-1]) if len(bars) else 0,
            }
        )
    return rows


def rankings(kind: str = "gainers", limit: int = 15) -> dict:
    rows = _rows_with_indicators()
    keymap = {
        "gainers": ("pct_chg", True),
        "losers": ("pct_chg", False),
        "turnover": ("turnover", True),
        "vol_ratio": ("vol_ratio", True),
        "inflow": ("main_net_inflow", True),
        "amount": ("amount", True),
    }
    key, desc = keymap.get(kind, ("pct_chg", True))
    rows.sort(key=lambda x: x[key], reverse=desc)
    items = [
        {
            "rank": i + 1,
            "ts_code": r["ts_code"],
            "name": r["name"],
            "industry": r["industry"],
            "close": round(float(r["close"]), 2),
            "pct_chg": round(float(r["pct_chg"]), 2),
            "turnover": round(float(r["turnover"]), 2),
            "vol_ratio": round(float(r["vol_ratio"]), 2),
            "main_net_inflow": round(float(r["main_net_inflow"]) / 1e4, 1),
            "amount": round(float(r["amount"]) / 1e8, 2),
        }
        for i, r in enumerate(rows[:limit])
    ]
    return {"kind": kind, "trade_date": date.today(), "items": items}


def limit_up_pool() -> dict:
    """涨停池 / 连板 / 炸板（演示合成）。"""
    rows = _rows_with_indicators()
    rng = np.random.default_rng(int(date.today().strftime("%Y%m%d")) + 7)
    pool = []
    for r in rows:
        if r["pct_chg"] >= 5.5:
            boards = int(rng.integers(1, 5))
            pool.append(
                {
                    "ts_code": r["ts_code"],
                    "name": r["name"],
                    "industry": r["industry"],
                    "pct_chg": round(float(r["pct_chg"]), 2),
                    "boards": boards,
                    "seal_amount": round(float(abs(rng.normal(2.2, 1.5))), 2),
                    "open_times": int(rng.integers(0, 3)),
                    "reason": rng.choice(["主题催化", "业绩预增", "资金抢筹", "板块联动"]),
                }
            )
    pool.sort(key=lambda x: (x["boards"], x["pct_chg"]), reverse=True)
    blast_rate = round(float(rng.uniform(12, 35)), 1)
    return {
        "trade_date": date.today(),
        "total": len(pool),
        "blast_rate": blast_rate,
        "max_boards": max((p["boards"] for p in pool), default=0),
        "items": pool,
    }


def dragon_tiger(limit: int = 12) -> dict:
    """龙虎榜（演示：机构/游资席位合成）。"""
    rows = _rows_with_indicators()
    rng = np.random.default_rng(int(date.today().strftime("%Y%m%d")) + 21)
    rows.sort(key=lambda x: abs(x["pct_chg"]), reverse=True)
    seats = ["机构专用", "沪股通", "深股通", "华鑫上海分公司", "国泰君安南京太平南路", "东财拉萨团结路"]
    items = []
    for r in rows[:limit]:
        buy = float(abs(rng.normal(1.8, 1.2)))
        sell = float(abs(rng.normal(1.2, 0.9)))
        items.append(
            {
                "ts_code": r["ts_code"],
                "name": r["name"],
                "pct_chg": round(float(r["pct_chg"]), 2),
                "reason": "日涨幅偏离值达7%" if r["pct_chg"] > 0 else "日跌幅偏离值达7%",
                "buy_total": round(buy, 2),
                "sell_total": round(sell, 2),
                "net": round(buy - sell, 2),
                "top_buyer": str(rng.choice(seats)),
                "top_seller": str(rng.choice(seats)),
                "institution_net": round(float(rng.normal(0.3, 0.8)), 2),
            }
        )
    return {"trade_date": date.today(), "items": items}


def sector_heatmap() -> dict:
    rows = _rows_with_indicators()
    sectors: dict[str, dict] = {}
    for r in rows:
        s = sectors.setdefault(
            r["industry"], {"name": r["industry"], "pct_sum": 0.0, "count": 0, "inflow": 0.0, "leader": None}
        )
        s["pct_sum"] += r["pct_chg"]
        s["count"] += 1
        s["inflow"] += r["main_net_inflow"]
        if s["leader"] is None or r["pct_chg"] > s["leader"]["pct_chg"]:
            s["leader"] = {"ts_code": r["ts_code"], "name": r["name"], "pct_chg": round(float(r["pct_chg"]), 2)}
    items = [
        {
            "name": v["name"],
            "avg_pct": round(v["pct_sum"] / max(1, v["count"]), 2),
            "count": v["count"],
            "inflow": round(v["inflow"] / 1e8, 2),
            "leader": v["leader"],
        }
        for v in sectors.values()
    ]
    items.sort(key=lambda x: x["avg_pct"], reverse=True)
    return {"trade_date": date.today(), "items": items}


def event_calendar(days: int = 10) -> dict:
    """财经日历：新股、财报、解禁、宏观（演示）。"""
    rng = np.random.default_rng(int(date.today().strftime("%Y%m%d")) + 42)
    provider = get_data_provider()
    stocks = provider.list_stocks(limit=30)
    kinds = [
        ("ipo", "新股申购"),
        ("earnings", "财报披露"),
        ("unlock", "限售解禁"),
        ("dividend", "分红除权"),
        ("macro", "宏观数据"),
    ]
    macro_events = ["PMI 公布", "CPI/PPI 公布", "LPR 报价", "社融数据", "美联储议息"]
    items = []
    for i in range(days):
        d = date.today() + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        n = int(rng.integers(1, 4))
        for _ in range(n):
            kind, label = kinds[int(rng.integers(0, len(kinds)))]
            if kind == "macro":
                title = str(rng.choice(macro_events))
                code, name = "", ""
            else:
                s = stocks[int(rng.integers(0, len(stocks)))]
                code, name = s["ts_code"], s["name"]
                title = f"{name} {label}"
            items.append(
                {
                    "date": str(d),
                    "kind": kind,
                    "label": label,
                    "title": title,
                    "ts_code": code,
                    "name": name,
                }
            )
    return {"start": str(date.today()), "items": items}


def research_reports(ts_code: str | None = None, limit: int = 12) -> dict:
    """研报中心（演示：机构评级与目标价合成）。"""
    provider = get_data_provider()
    stocks = provider.list_stocks(limit=40)
    if ts_code:
        stocks = [s for s in stocks if s["ts_code"] == ts_code] or stocks[:1]
    orgs = ["中金公司", "中信证券", "国泰海通", "华泰证券", "招商证券", "广发证券", "东方财富证券"]
    ratings = ["买入", "增持", "中性", "增持", "买入"]
    now = datetime.utcnow()
    items = []
    for i in range(limit):
        s = stocks[i % len(stocks)]
        rng = np.random.default_rng(abs(hash(s["ts_code"] + str(i))) % (2**32))
        bars = provider.get_daily_bars(s["ts_code"], days=5)
        close = float(bars["close"].iloc[-1]) if len(bars) else 50.0
        rating = ratings[int(rng.integers(0, len(ratings)))]
        upside = float(rng.uniform(0.05, 0.35)) if rating in ("买入", "增持") else float(rng.uniform(-0.05, 0.1))
        items.append(
            {
                "id": f"rpt-{i}",
                "ts_code": s["ts_code"],
                "name": s["name"],
                "title": f"{s['name']}：{rng.choice(['业绩符合预期', '景气度向上', '新品周期开启', '估值修复可期', '龙头地位稳固'])}",
                "org": str(rng.choice(orgs)),
                "rating": rating,
                "target_price": round(close * (1 + upside), 2),
                "eps_forecast": round(float(abs(rng.normal(2.5, 1.5))), 2),
                "published_at": (now - timedelta(hours=int(rng.integers(2, 96)))).isoformat() + "Z",
            }
        )
    return {"items": items}


def company_profile(ts_code: str) -> dict:
    """F10：公司概况 / 股东 / 高管 / 主营（演示）。"""
    provider = get_data_provider()
    meta = provider.resolve_name(ts_code)
    fund = provider.get_fundamentals(meta["ts_code"])
    rng = np.random.default_rng(abs(hash(meta["ts_code"] + ":f10")) % (2**32))
    holders = [
        {"name": f"{meta['name']}集团有限公司", "ratio": round(float(rng.uniform(18, 45)), 2), "change": "不变"},
        {"name": "香港中央结算有限公司", "ratio": round(float(rng.uniform(2, 8)), 2), "change": rng.choice(["增持", "减持", "不变"])},
        {"name": "中央汇金资产管理", "ratio": round(float(rng.uniform(0.8, 3)), 2), "change": "不变"},
        {"name": "全国社保基金一一八组合", "ratio": round(float(rng.uniform(0.5, 2)), 2), "change": rng.choice(["新进", "增持", "不变"])},
        {"name": "某公募基金组合", "ratio": round(float(rng.uniform(0.5, 2.5)), 2), "change": rng.choice(["增持", "减持"])},
    ]
    total_share = round(float(rng.uniform(8, 180)), 2)
    return {
        "ts_code": meta["ts_code"],
        "name": meta["name"],
        "industry": meta.get("industry", ""),
        "profile": {
            "main_business": f"{meta.get('industry','综合')}相关产品的研发、生产与销售",
            "list_date": meta.get("list_date", "20100101"),
            "total_share": total_share,
            "float_share": round(total_share * float(rng.uniform(0.6, 0.95)), 2),
            "employees": int(rng.integers(2000, 80000)),
            "chairman": "示例董事长",
            "region": str(rng.choice(["上海", "深圳", "北京", "杭州", "广州"])),
        },
        "valuation": {
            "pe": fund["pe"],
            "pb": fund["pb"],
            "ps": fund["ps"],
            "dividend_yield": fund["dividend_yield"],
            "total_mv": round(total_share * float(rng.uniform(8, 60)), 1),
        },
        "finance": {
            "roe": fund["roe"],
            "gross_margin": fund["gross_margin"],
            "net_margin": fund["net_margin"],
            "debt_ratio": fund["debt_ratio"],
            "revenue_growth": fund["revenue_growth"],
            "profit_growth": fund["profit_growth"],
        },
        "top_holders": holders,
        "pledge_ratio": round(float(abs(rng.normal(5, 4))), 2),
        "unlock_next": {
            "date": str(date.today() + timedelta(days=int(rng.integers(20, 180)))),
            "ratio": round(float(rng.uniform(0.5, 8)), 2),
        },
    }


def kline(ts_code: str, days: int = 120) -> dict:
    provider = get_data_provider()
    meta = provider.resolve_name(ts_code)
    bars = provider.get_daily_bars(meta["ts_code"], days=days)
    ind = compute_indicators(bars)
    return {
        "ts_code": meta["ts_code"],
        "name": meta["name"],
        "industry": meta.get("industry", ""),
        "bars": [
            {
                "date": str(r["trade_date"]),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "vol": float(r["vol"]),
                "pct_chg": float(r["pct_chg"]),
            }
            for _, r in bars.iterrows()
        ],
        "indicators": {k: v for k, v in ind.items() if k != "series"},
    }