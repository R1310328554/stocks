"""多专家 Agent 协同：宏观 / 产业 / 财报 / 技术 / 风控。"""

from __future__ import annotations

from datetime import datetime

from app.services.datasources import get_data_provider
from app.services.diagnosis import diagnose_stock
from app.services.sentiment import analyze_capital_flow
from app.services.strategies import MultiFactorPicker


def run_multi_agent_research(ts_code: str | None = None, question: str = "") -> dict:
    provider = get_data_provider()
    overview = provider.get_market_overview()
    picks = MultiFactorPicker().run(top_n=5)

    macro = {
        "agent": "宏观分析专家",
        "summary": (
            f"市场情绪 {overview['fear_greed_label']}（{overview['fear_greed']}），"
            f"北向净流入 {overview['northbound_net']} 亿，两融变化 {overview['margin_balance_change']} 亿。"
        ),
        "stance": "偏多" if overview["fear_greed"] >= 55 else "中性" if overview["fear_greed"] >= 40 else "谨慎",
        "points": [
            f"热点板块：{', '.join(s['name'] for s in overview['hot_sectors'][:3])}",
            f"涨跌停比 {overview['limit_up_count']}:{overview['limit_down_count']}",
            overview["commentary"],
        ],
    }

    industry = {
        "agent": "产业链研究专家",
        "summary": "围绕当前强势主题与龙头溢价，筛选具备景气与资金共振的方向。",
        "stance": "聚焦主线",
        "points": [
            f"关注 {p['industry']} / {p['name']}（综合分 {p['total_score']}）"
            for p in picks["items"][:3]
        ]
        or ["暂无显著产业主线"],
    }

    target = ts_code or (picks["items"][0]["ts_code"] if picks["items"] else "600519.SH")
    report = diagnose_stock(target)
    capital = analyze_capital_flow(target)

    fundamental = {
        "agent": "财报解读专家",
        "summary": report["fundamental"]["summary"],
        "stance": report["fundamental"]["level"],
        "points": report["fundamental"]["details"],
    }
    technical = {
        "agent": "技术回测专家",
        "summary": report["technical"]["summary"],
        "stance": report["technical"]["level"],
        "points": report["technical"]["details"] + report.get("signals", [])[:3],
    }
    risk = {
        "agent": "风控合规专家",
        "summary": "汇总财务、估值、拥挤度与波动风险，给出仓位约束。",
        "stance": "严控回撤",
        "points": report["risks"] + [capital["summary"], report.get("advice", {}).get("risk_note", "")],
    }

    # 主 Agent 统筹
    scores = [
        report["overall_score"],
        overview["fear_greed"],
        70 if "看多" in capital["consensus"] else 45,
    ]
    consensus_score = round(sum(scores) / len(scores), 1)
    if consensus_score >= 65:
        decision = "多专家偏乐观：可按建议仓位分批配置，严格止损。"
    elif consensus_score >= 50:
        decision = "多专家分歧中性：以观察和轻仓验证为主。"
    else:
        decision = "多专家偏谨慎：优先防守，等待更佳赔率。"

    return {
        "question": question or f"对 {report['name']} 及当前市场的综合研判",
        "target": {"ts_code": report["ts_code"], "name": report["name"]},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "consensus_score": consensus_score,
        "decision": decision,
        "experts": [macro, industry, fundamental, technical, risk],
        "linked_picks": picks["items"][:5],
        "trade_advice": report.get("advice"),
    }