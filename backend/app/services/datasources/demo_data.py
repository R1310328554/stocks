"""演示数据生成器：无外部密钥时保证平台可完整演示."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache

import numpy as np
import pandas as pd


UNIVERSE = [
    ("600519.SH", "600519", "贵州茅台", "白酒", "主板"),
    ("000858.SZ", "000858", "五粮液", "白酒", "主板"),
    ("601318.SH", "601318", "中国平安", "保险", "主板"),
    ("600036.SH", "600036", "招商银行", "银行", "主板"),
    ("000333.SZ", "000333", "美的集团", "家电", "主板"),
    ("002415.SZ", "002415", "海康威视", "安防", "主板"),
    ("300750.SZ", "300750", "宁德时代", "电池", "创业板"),
    ("601012.SH", "601012", "隆基绿能", "光伏", "主板"),
    ("002594.SZ", "002594", "比亚迪", "汽车", "主板"),
    ("600276.SH", "600276", "恒瑞医药", "医药", "主板"),
    ("000661.SZ", "000661", "长春高新", "医药", "主板"),
    ("603259.SH", "603259", "药明康德", "医药", "主板"),
    ("688981.SH", "688981", "中芯国际", "半导体", "科创板"),
    ("002230.SZ", "002230", "科大讯飞", "人工智能", "主板"),
    ("300059.SZ", "300059", "东方财富", "证券", "创业板"),
    ("601888.SH", "601888", "中国中免", "免税", "主板"),
    ("600887.SH", "600887", "伊利股份", "食品", "主板"),
    ("000568.SZ", "000568", "泸州老窖", "白酒", "主板"),
    ("601166.SH", "601166", "兴业银行", "银行", "主板"),
    ("600030.SH", "600030", "中信证券", "证券", "主板"),
    ("002475.SZ", "002475", "立讯精密", "电子", "主板"),
    ("300124.SZ", "300124", "汇川技术", "工控", "创业板"),
    ("603501.SH", "603501", "韦尔股份", "半导体", "主板"),
    ("688111.SH", "688111", "金山办公", "软件", "科创板"),
    ("002352.SZ", "002352", "顺丰控股", "物流", "主板"),
    ("601899.SH", "601899", "紫金矿业", "有色", "主板"),
    ("600585.SH", "600585", "海螺水泥", "建材", "主板"),
    ("000725.SZ", "000725", "京东方A", "显示面板", "主板"),
    ("002714.SZ", "002714", "牧原股份", "养殖", "主板"),
    ("600031.SH", "600031", "三一重工", "机械", "主板"),
    ("601668.SH", "601668", "中国建筑", "建筑", "主板"),
    ("600900.SH", "600900", "长江电力", "电力", "主板"),
    ("000001.SZ", "000001", "平安银行", "银行", "主板"),
    ("601398.SH", "601398", "工商银行", "银行", "主板"),
    ("600048.SH", "600048", "保利发展", "地产", "主板"),
    ("002304.SZ", "002304", "洋河股份", "白酒", "主板"),
    ("600809.SH", "600809", "山西汾酒", "白酒", "主板"),
    ("300014.SZ", "300014", "亿纬锂能", "电池", "创业板"),
    ("002460.SZ", "002460", "赣锋锂业", "锂电", "主板"),
    ("601633.SH", "601633", "长城汽车", "汽车", "主板"),
    ("000625.SZ", "000625", "长安汽车", "汽车", "主板"),
    ("600104.SH", "600104", "上汽集团", "汽车", "主板"),
    ("601012.SH", "601012", "隆基绿能", "光伏", "主板"),
    ("300274.SZ", "300274", "阳光电源", "光伏", "创业板"),
    ("688012.SH", "688012", "中微公司", "半导体", "科创板"),
    ("002241.SZ", "002241", "歌尔股份", "电子", "主板"),
    ("600570.SH", "600570", "恒生电子", "软件", "主板"),
    ("000977.SZ", "000977", "浪潮信息", "计算机", "主板"),
    ("603019.SH", "603019", "中科曙光", "计算机", "主板"),
    ("300760.SZ", "300760", "迈瑞医疗", "医疗器械", "创业板"),
]


def _seed_for(code: str) -> int:
    return abs(hash(code)) % (2**32)


@lru_cache(maxsize=1)
def list_stocks() -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for ts_code, symbol, name, industry, market in UNIVERSE:
        if ts_code in seen:
            continue
        seen.add(ts_code)
        rows.append(
            {
                "ts_code": ts_code,
                "symbol": symbol,
                "name": name,
                "industry": industry,
                "market": market,
                "list_date": "20100101",
            }
        )
    return rows


def generate_daily_bars(ts_code: str, days: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(_seed_for(ts_code))
    end = date.today()
    # 跳过周末的简化交易日
    dates: list[date] = []
    cursor = end
    while len(dates) < days:
        if cursor.weekday() < 5:
            dates.append(cursor)
        cursor -= timedelta(days=1)
    dates = list(reversed(dates))

    base = 20 + (rng.random() * 180)
    drift = rng.normal(0.0004, 0.0008)
    rets = rng.normal(drift, 0.018, size=len(dates))
    closes = base * np.cumprod(1 + rets)
    opens = closes * (1 + rng.normal(0, 0.004, size=len(dates)))
    highs = np.maximum(opens, closes) * (1 + rng.uniform(0.002, 0.02, size=len(dates)))
    lows = np.minimum(opens, closes) * (1 - rng.uniform(0.002, 0.02, size=len(dates)))
    vols = rng.uniform(5e5, 8e6, size=len(dates))
    amounts = vols * closes
    pct = np.concatenate([[0.0], np.diff(closes) / closes[:-1] * 100])

    return pd.DataFrame(
        {
            "ts_code": ts_code,
            "trade_date": dates,
            "open": np.round(opens, 2),
            "high": np.round(highs, 2),
            "low": np.round(lows, 2),
            "close": np.round(closes, 2),
            "vol": np.round(vols, 0),
            "amount": np.round(amounts, 2),
            "pct_chg": np.round(pct, 2),
        }
    )


def fundamental_snapshot(ts_code: str) -> dict:
    rng = np.random.default_rng(_seed_for(ts_code + ":fund"))
    pe = float(np.clip(rng.normal(28, 18), 5, 120))
    pb = float(np.clip(rng.normal(3.2, 1.8), 0.6, 15))
    ps = float(np.clip(rng.normal(4.5, 2.5), 0.5, 20))
    roe = float(np.clip(rng.normal(14, 8), -5, 40))
    roa = float(np.clip(roe * 0.45, -3, 25))
    gross_margin = float(np.clip(rng.normal(32, 12), 5, 75))
    net_margin = float(np.clip(rng.normal(12, 7), -8, 40))
    debt_ratio = float(np.clip(rng.normal(48, 15), 10, 85))
    revenue_growth = float(np.clip(rng.normal(18, 20), -30, 80))
    profit_growth = float(np.clip(rng.normal(22, 25), -40, 100))
    eps_growth = float(np.clip(rng.normal(20, 22), -35, 90))
    dividend_yield = float(np.clip(rng.normal(1.8, 1.2), 0, 6))
    turnover = float(np.clip(rng.normal(2.4, 1.5), 0.3, 12))
    return {
        "ts_code": ts_code,
        "pe": round(pe, 2),
        "pb": round(pb, 2),
        "ps": round(ps, 2),
        "pcf": round(pe * 0.7, 2),
        "roe": round(roe, 2),
        "roa": round(roa, 2),
        "gross_margin": round(gross_margin, 2),
        "net_margin": round(net_margin, 2),
        "debt_ratio": round(debt_ratio, 2),
        "revenue_growth": round(revenue_growth, 2),
        "profit_growth": round(profit_growth, 2),
        "eps_growth": round(eps_growth, 2),
        "dividend_yield": round(dividend_yield, 2),
        "turnover": round(turnover, 2),
        "main_net_inflow": round(float(rng.normal(0, 3e7)), 0),
        "northbound_change": round(float(rng.normal(0, 0.35)), 3),
        "margin_balance_change": round(float(rng.normal(0, 2e7)), 0),
        "block_premium": round(float(rng.normal(0, 2.5)), 2),
    }


def market_overview() -> dict:
    rng = np.random.default_rng(int(date.today().strftime("%Y%m%d")))
    fear = float(np.clip(rng.normal(52, 15), 5, 95))
    label = (
        "极度恐慌"
        if fear < 20
        else "偏恐慌"
        if fear < 40
        else "中性"
        if fear < 60
        else "偏贪婪"
        if fear < 80
        else "极度贪婪"
    )
    sectors = [
        ("白酒", rng.uniform(-1, 3)),
        ("半导体", rng.uniform(-2, 4)),
        ("新能源", rng.uniform(-2.5, 3.5)),
        ("银行", rng.uniform(-1, 1.5)),
        ("医药", rng.uniform(-1.5, 2.5)),
        ("人工智能", rng.uniform(-2, 4.5)),
        ("消费电子", rng.uniform(-2, 3)),
        ("有色", rng.uniform(-2.5, 3)),
    ]
    sectors.sort(key=lambda x: x[1], reverse=True)
    return {
        "trade_date": date.today(),
        "index_summary": [
            {"name": "上证指数", "close": 3125.4 + rng.normal(0, 18), "pct_chg": round(float(rng.normal(0.1, 0.8)), 2)},
            {"name": "深证成指", "close": 9850.2 + rng.normal(0, 55), "pct_chg": round(float(rng.normal(0.15, 1.0)), 2)},
            {"name": "创业板指", "close": 1920.8 + rng.normal(0, 28), "pct_chg": round(float(rng.normal(0.2, 1.3)), 2)},
        ],
        "hot_sectors": [
            {"name": n, "pct_chg": round(float(v), 2)} for n, v in sectors[:6]
        ],
        "limit_up_count": int(rng.integers(20, 80)),
        "limit_down_count": int(rng.integers(5, 35)),
        "northbound_net": round(float(rng.normal(18, 45)), 2),
        "margin_balance_change": round(float(rng.normal(12, 40)), 2),
        "fear_greed": round(fear, 1),
        "fear_greed_label": label,
        "commentary": "演示模式：综合指数波动、板块轮动与资金情绪生成市场快照，便于体验选股闭环。",
    }


def news_feed(limit: int = 20) -> list[dict]:
    titles = [
        "央行公开市场操作回笼流动性，短端利率小幅上行",
        "新能源车渗透率再创新高，产业链中游盈利改善",
        "半导体设备国产替代加速，政策支持力度加大",
        "白酒龙头渠道库存健康，旺季动销好于预期",
        "北向资金连续净流入，聚焦高端制造与消费",
        "上市公司半年报披露进入高峰，绩优股受关注",
        "大宗交易折价成交增多，机构调仓迹象显现",
        "人工智能应用落地加速，算力与软件板块活跃",
    ]
    now = datetime.utcnow()
    stocks = list_stocks()
    rows = []
    for i in range(limit):
        s = stocks[i % len(stocks)]
        rows.append(
            {
                "id": f"news-{i}",
                "title": titles[i % len(titles)],
                "source": "演示资讯",
                "ts_code": s["ts_code"],
                "name": s["name"],
                "published_at": (now - timedelta(minutes=25 * i)).isoformat() + "Z",
            }
        )
    return rows


def alerts(limit: int = 15) -> list[dict]:
    types = [
        ("price_spike", "股价快速拉升", "high"),
        ("volume_surge", "成交量异动放量", "medium"),
        ("capital_inflow", "主力大单净流入突增", "high"),
        ("announcement", "相关公告发布", "medium"),
        ("breakout", "突破关键均线压力", "medium"),
    ]
    stocks = list_stocks()
    now = datetime.utcnow()
    rows = []
    for i in range(limit):
        t, msg, sev = types[i % len(types)]
        s = stocks[(i * 3) % len(stocks)]
        rows.append(
            {
                "id": f"alert-{i}",
                "ts_code": s["ts_code"],
                "name": s["name"],
                "alert_type": t,
                "message": f"{s['name']} {msg}",
                "severity": sev,
                "created_at": now - timedelta(minutes=8 * i),
            }
        )
    return rows