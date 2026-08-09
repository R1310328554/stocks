"""权威数据源注册表：标注来源层级、用途与接入状态。"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class DataSourceMeta:
    id: str
    name: str
    tier: str  # L1交易所/监管 L2机构终端 L3主流资讯 L4衍生
    authority: str
    coverage: list[str]
    access: str
    status: str  # live | configured | demo_fallback
    notes: str


SOURCES: list[DataSourceMeta] = [
    DataSourceMeta(
        id="sse_szse",
        name="上交所/深交所官方行情与两融",
        tier="L1",
        authority="交易所一级",
        coverage=["日线", "停牌", "融资融券", "ETF申赎清单"],
        access="官方接口/合作行情商",
        status="demo_fallback",
        notes="实盘应优先交易所或持牌行情商",
    ),
    DataSourceMeta(
        id="tushare",
        name="Tushare Pro",
        tier="L2",
        authority="主流量化数据平台",
        coverage=["行情", "财务", "估值", "指数", "基金", "债券"],
        access="HTTP SDK + Token",
        status="configured",
        notes="配置 TUSHARE_TOKEN 后自动启用",
    ),
    DataSourceMeta(
        id="cninfo",
        name="巨潮资讯 CNINFO",
        tier="L1",
        authority="证监会指定信息披露",
        coverage=["公告", "年报", "招股说明书"],
        access="HTTP API",
        status="demo_fallback",
        notes="公告与披露文本权威来源",
    ),
    DataSourceMeta(
        id="akshare",
        name="akshare（东财/同花顺聚合）",
        tier="L3",
        authority="开源聚合，适合探索与校验",
        coverage=["热点", "龙虎榜", "资金流", "基金净值"],
        access="Python 库",
        status="demo_fallback",
        notes="免费覆盖广，需做清洗与交叉验证",
    ),
    DataSourceMeta(
        id="eastmoney",
        name="东方财富",
        tier="L3",
        authority="主流资讯与研报",
        coverage=["研报", "资金流向", "ETF/LOF", "债券"],
        access="HTTP/Cookie",
        status="demo_fallback",
        notes="研报与场内基金常用源",
    ),
    DataSourceMeta(
        id="chinabond",
        name="中国债券信息网/中债估值",
        tier="L1",
        authority="债券市场权威估值",
        coverage=["国债", "信用债", "收益率曲线"],
        access="官方/终端",
        status="demo_fallback",
        notes="债券推荐以中债估值与久期风险为核心",
    ),
    DataSourceMeta(
        id="wind",
        name="Wind",
        tier="L2",
        authority="机构级基准终端",
        coverage=["全品种", "一致预期", "组合分析"],
        access="企业 SDK",
        status="demo_fallback",
        notes="持牌机构场景可替换为 Wind",
    ),
]


def list_sources(live_enabled: bool = False) -> list[dict]:
    rows = []
    for s in SOURCES:
        item = asdict(s)
        if s.id == "tushare" and live_enabled:
            item["status"] = "live"
        rows.append(item)
    return rows


def source_health(live_enabled: bool = False) -> dict:
    rows = list_sources(live_enabled)
    live = sum(1 for r in rows if r["status"] == "live")
    configured = sum(1 for r in rows if r["status"] == "configured")
    demo = sum(1 for r in rows if r["status"] == "demo_fallback")
    return {
        "total": len(rows),
        "live": live,
        "configured": configured,
        "demo_fallback": demo,
        "reliability_score": round(min(100, 55 + live * 12 + configured * 6), 1),
        "items": rows,
        "guidance": "生产环境建议：交易所/巨潮(L1) + Tushare/Wind(L2) 双源校验，资讯源做延迟与完整性监控。",
    }