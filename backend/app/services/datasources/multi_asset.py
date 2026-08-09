"""多资产演示宇宙：股票 / ETF / LOF / 基金 / 债券。"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.services.datasources.demo_data import generate_daily_bars, list_stocks


ETFS = [
    ("510300.SH", "510300", "沪深300ETF", "宽基", "ETF", "华泰柏瑞"),
    ("510500.SH", "510500", "中证500ETF", "宽基", "ETF", "南方"),
    ("159915.SZ", "159915", "创业板ETF", "成长", "ETF", "易方达"),
    ("512880.SH", "512880", "证券ETF", "行业", "ETF", "国泰"),
    ("512690.SH", "512690", "酒ETF", "消费", "ETF", "鹏华"),
    ("515790.SH", "515790", "光伏ETF", "新能源", "ETF", "华泰柏瑞"),
    ("512480.SH", "512480", "半导体ETF", "科技", "ETF", "国联安"),
    ("159819.SZ", "159819", "人工智能ETF", "科技", "ETF", "易方达"),
    ("511010.SH", "511010", "国债ETF", "利率", "ETF", "国泰"),
    ("518880.SH", "518880", "黄金ETF", "商品", "ETF", "华安"),
    ("513100.SH", "513100", "纳指ETF", "海外", "ETF", "国泰"),
    ("159920.SZ", "159920", "恒生ETF", "海外", "ETF", "华夏"),
]

LOFS = [
    ("161725.SZ", "161725", "招商中证白酒", "消费", "LOF", "招商基金"),
    ("160632.SZ", "160632", "鹏华酒", "消费", "LOF", "鹏华基金"),
    ("163406.SZ", "163406", "兴全合润", "混合", "LOF", "兴证全球"),
    ("161005.SZ", "161005", "富国天惠成长", "成长", "LOF", "富国基金"),
    ("160222.SZ", "160222", "国泰国证食品饮料", "消费", "LOF", "国泰基金"),
    ("162411.SZ", "162411", "华宝标普油气", "商品", "LOF", "华宝基金"),
]

FUNDS = [
    ("000001.OF", "000001", "华夏成长混合", "混合型", "Fund", "华夏基金"),
    ("110022.OF", "110022", "易方达消费行业", "股票型", "Fund", "易方达"),
    ("163406.OF", "163406", "兴全合润混合", "混合型", "Fund", "兴证全球"),
    ("005827.OF", "005827", "易方达蓝筹精选", "股票型", "Fund", "易方达"),
    ("161725.OF", "161725", "招商中证白酒指数", "指数型", "Fund", "招商基金"),
    ("000216.OF", "000216", "华安黄金易联接", "商品型", "Fund", "华安基金"),
    ("003095.OF", "003095", "中欧医疗健康", "行业主题", "Fund", "中欧基金"),
    ("001938.OF", "001938", "中欧时代先锋", "成长", "Fund", "中欧基金"),
    ("110011.OF", "110011", "易方达优质精选", "混合型", "Fund", "易方达"),
    ("270002.OF", "270002", "广发稳健增长", "混合型", "Fund", "广发基金"),
]

BONDS = [
    ("019666.SH", "019666", "22国债01", "国债", "Bond", "财政部"),
    ("019740.SH", "019740", "24国债13", "国债", "Bond", "财政部"),
    ("230023.IB", "230023", "23附息国债23", "利率债", "Bond", "财政部"),
    ("102280123.IB", "102280123", "22鲁高AAA", "信用债", "Bond", "山东高速"),
    ("136641.SH", "136641", "16宝钢MTN001", "信用债", "Bond", "宝钢股份"),
    ("127017.SZ", "127017", "可转债示例", "可转债", "Bond", "上市公司"),
]


def _seed(code: str) -> int:
    return abs(hash(code)) % (2**32)


@lru_cache(maxsize=1)
def list_etfs() -> list[dict]:
    return [
        {
            "ts_code": c,
            "symbol": s,
            "name": n,
            "industry": ind,
            "asset_type": t,
            "manager": m,
            "market": "场内",
        }
        for c, s, n, ind, t, m in ETFS
    ]


@lru_cache(maxsize=1)
def list_lofs() -> list[dict]:
    return [
        {
            "ts_code": c,
            "symbol": s,
            "name": n,
            "industry": ind,
            "asset_type": t,
            "manager": m,
            "market": "场内",
        }
        for c, s, n, ind, t, m in LOFS
    ]


@lru_cache(maxsize=1)
def list_funds() -> list[dict]:
    return [
        {
            "ts_code": c,
            "symbol": s,
            "name": n,
            "industry": ind,
            "asset_type": t,
            "manager": m,
            "market": "场外",
        }
        for c, s, n, ind, t, m in FUNDS
    ]


@lru_cache(maxsize=1)
def list_bonds() -> list[dict]:
    return [
        {
            "ts_code": c,
            "symbol": s,
            "name": n,
            "industry": ind,
            "asset_type": t,
            "manager": m,
            "market": "固收",
        }
        for c, s, n, ind, t, m in BONDS
    ]


def list_assets(asset_type: str | None = None, limit: int | None = None) -> list[dict]:
    mapping = {
        "stock": [{**x, "asset_type": "Stock"} for x in list_stocks()],
        "etf": list_etfs(),
        "lof": list_lofs(),
        "fund": list_funds(),
        "bond": list_bonds(),
    }
    if asset_type:
        rows = mapping.get(asset_type.lower(), [])
    else:
        rows = []
        for v in mapping.values():
            rows.extend(v)
    return rows[:limit] if limit else rows


def asset_metrics(ts_code: str, asset_type: str) -> dict:
    rng = np.random.default_rng(_seed(ts_code + asset_type))
    bars = generate_daily_bars(ts_code, days=120)
    close = float(bars["close"].iloc[-1])
    pct = float(bars["pct_chg"].iloc[-1])
    ret_20 = float(bars["close"].iloc[-1] / bars["close"].iloc[-21] - 1) * 100 if len(bars) > 21 else 0
    ret_60 = float(bars["close"].iloc[-1] / bars["close"].iloc[-61] - 1) * 100 if len(bars) > 61 else 0
    vol = float(bars["close"].pct_change().std() * np.sqrt(252) * 100)

    base = {
        "ts_code": ts_code,
        "asset_type": asset_type,
        "close": round(close, 3),
        "pct_chg": round(pct, 2),
        "ret_20": round(ret_20, 2),
        "ret_60": round(ret_60, 2),
        "volatility": round(vol, 2),
        "liquidity_score": round(float(np.clip(rng.normal(70, 12), 30, 98)), 1),
    }

    if asset_type in {"ETF", "LOF", "Fund"}:
        base.update(
            {
                "nav": round(close * float(rng.uniform(0.995, 1.005)), 4),
                "premium": round(float(rng.normal(0.1, 0.35)), 2),
                "tracking_error": round(float(abs(rng.normal(0.8, 0.4))), 2),
                "expense_ratio": round(float(np.clip(rng.normal(0.55, 0.2), 0.15, 1.5)), 2),
                "sharpe": round(float(rng.normal(0.9, 0.45)), 2),
                "max_drawdown": round(float(abs(rng.normal(12, 6))), 2),
                "ytd_return": round(float(rng.normal(8, 12)), 2),
                "manager_score": round(float(np.clip(rng.normal(72, 10), 40, 95)), 1),
            }
        )
    if asset_type == "Bond":
        base.update(
            {
                "ytm": round(float(np.clip(rng.normal(2.6, 0.7), 1.2, 5.5)), 2),
                "duration": round(float(np.clip(rng.normal(4.2, 1.8), 0.5, 12)), 2),
                "credit_rating": rng.choice(["AAA", "AA+", "AA", "AA-"]),
                "spread_bp": round(float(abs(rng.normal(45, 25))), 1),
                "coupon": round(float(np.clip(rng.normal(2.8, 0.6), 1.5, 5)), 2),
            }
        )
    return base


def resolve_asset(code: str) -> dict:
    for row in list_assets():
        if row["ts_code"] == code or row["symbol"] == code:
            return row
    return {
        "ts_code": code,
        "symbol": code.split(".")[0],
        "name": code,
        "industry": "未知",
        "asset_type": "Stock",
        "manager": "",
        "market": "",
    }