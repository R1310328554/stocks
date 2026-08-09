"""自然语言选股：规则解析常见条件（可平滑替换为 LLM）."""

from __future__ import annotations

import re


def parse_natural_language_filters(query: str) -> dict:
    q = query.strip()
    filters: dict = {"raw_query": q}

    pe = re.search(r"(?:市盈率|PE|pe)\s*(?:小于|低于|<|<=)\s*(\d+(?:\.\d+)?)", q)
    if pe:
        filters["max_pe"] = float(pe.group(1))

    roe = re.search(r"(?:ROE|roe|净资产收益率)\s*(?:大于|高于|>|>=)\s*(\d+(?:\.\d+)?)", q)
    if roe:
        filters["min_roe"] = float(roe.group(1))

    growth = re.search(
        r"(?:净利润增长|净利增长|利润增长)\s*(?:大于|高于|>|>=)\s*(\d+(?:\.\d+)?)",
        q,
    )
    if growth:
        filters["min_profit_growth"] = float(growth.group(1))

    industries = []
    for name in ["白酒", "银行", "医药", "半导体", "光伏", "汽车", "人工智能", "电池", "证券", "软件"]:
        if name in q:
            industries.append(name)
    if industries:
        filters["industries"] = industries

    if "创业板" in q:
        filters["market"] = "创业板"
    elif "科创板" in q:
        filters["market"] = "科创板"
    elif "主板" in q:
        filters["market"] = "主板"

    patterns = []
    if "双底" in q:
        patterns.append("疑似双底")
    if "放量" in q or "突破" in q:
        patterns.append("放量突破")
    if "三角" in q:
        patterns.append("三角形收敛")
    if patterns:
        filters["require_patterns"] = patterns

    top = re.search(r"(?:前|Top|top)\s*(\d+)", q)
    if top:
        filters["top_n"] = int(top.group(1))

    return filters