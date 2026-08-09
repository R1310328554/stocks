"""技术指标与经典形态识别."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def compute_indicators(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["vol"].astype(float)

    ma5 = close.rolling(5).mean()
    ma10 = close.rolling(10).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    dif = ema12 - ema26
    dea = _ema(dif, 9)
    macd = (dif - dea) * 2

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    mid = ma20
    std = close.rolling(20).std()
    upper = mid + 2 * std
    lower = mid - 2 * std

    # 神奇九转（简化 TD Sequential）
    td_up = 0
    td_down = 0
    closes = close.to_list()
    for i in range(4, len(closes)):
        if closes[i] > closes[i - 4]:
            td_up = td_up + 1 if td_up >= 0 else 1
            td_down = 0
        elif closes[i] < closes[i - 4]:
            td_down = td_down + 1 if td_down >= 0 else 1
            td_up = 0
        else:
            td_up = 0
            td_down = 0

    last = len(close) - 1
    ret_5 = float(close.iloc[last] / close.iloc[max(0, last - 5)] - 1) if last >= 5 else 0.0
    ret_20 = float(close.iloc[last] / close.iloc[max(0, last - 20)] - 1) if last >= 20 else 0.0
    ret_60 = float(close.iloc[last] / close.iloc[max(0, last - 60)] - 1) if last >= 60 else 0.0
    vol_ratio = float(vol.iloc[last] / vol.rolling(20).mean().iloc[last]) if last >= 20 else 1.0
    volatility = float(close.pct_change().rolling(20).std().iloc[last] * np.sqrt(252) * 100) if last >= 20 else 0.0

    signals: list[str] = []
    if last >= 1:
        if ma5.iloc[last] > ma20.iloc[last] and ma5.iloc[last - 1] <= ma20.iloc[last - 1]:
            signals.append("MA5上穿MA20（金叉）")
        if ma5.iloc[last] < ma20.iloc[last] and ma5.iloc[last - 1] >= ma20.iloc[last - 1]:
            signals.append("MA5下穿MA20（死叉）")
        if dif.iloc[last] > dea.iloc[last] and dif.iloc[last - 1] <= dea.iloc[last - 1]:
            signals.append("MACD金叉")
        if dif.iloc[last] < dea.iloc[last] and dif.iloc[last - 1] >= dea.iloc[last - 1]:
            signals.append("MACD死叉")
    rsi_v = float(rsi.iloc[last]) if not np.isnan(rsi.iloc[last]) else 50.0
    if rsi_v >= 70:
        signals.append("RSI超买")
    elif rsi_v <= 30:
        signals.append("RSI超卖")
    if close.iloc[last] > upper.iloc[last]:
        signals.append("突破布林上轨")
    elif close.iloc[last] < lower.iloc[last]:
        signals.append("跌破布林下轨")
    if td_up >= 9:
        signals.append("神奇九转：上涨九转（关注回调）")
    if td_down >= 9:
        signals.append("神奇九转：下跌九转（关注反弹）")

    return {
        "close": float(close.iloc[last]),
        "pct_chg": float(df["pct_chg"].iloc[last]) if "pct_chg" in df else 0.0,
        "ma5": _f(ma5.iloc[last]),
        "ma10": _f(ma10.iloc[last]),
        "ma20": _f(ma20.iloc[last]),
        "ma60": _f(ma60.iloc[last]),
        "macd_dif": _f(dif.iloc[last]),
        "macd_dea": _f(dea.iloc[last]),
        "macd": _f(macd.iloc[last]),
        "rsi14": round(rsi_v, 2),
        "boll_upper": _f(upper.iloc[last]),
        "boll_mid": _f(mid.iloc[last]),
        "boll_lower": _f(lower.iloc[last]),
        "td_up": td_up,
        "td_down": td_down,
        "ret_5": round(ret_5 * 100, 2),
        "ret_20": round(ret_20 * 100, 2),
        "ret_60": round(ret_60 * 100, 2),
        "vol_ratio": round(vol_ratio, 2),
        "volatility": round(volatility, 2),
        "signals": signals,
        "series": {
            "dates": [str(d) for d in df["trade_date"].tolist()[-60:]],
            "close": [float(x) for x in close.tolist()[-60:]],
            "ma20": [_f(x) for x in ma20.tolist()[-60:]],
            "macd": [_f(x) for x in macd.tolist()[-60:]],
            "rsi": [_f(x) if not np.isnan(x) else 50.0 for x in rsi.tolist()[-60:]],
        },
    }


def detect_patterns(df: pd.DataFrame) -> list[str]:
    """轻量形态识别：双底/双顶、三角收敛、放量突破."""
    if df is None or len(df) < 40:
        return []
    close = df["close"].astype(float).to_numpy()
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    vol = df["vol"].astype(float).to_numpy()
    patterns: list[str] = []

    window = close[-40:]
    mid = 20
    left_min = float(np.min(window[:mid]))
    right_min = float(np.min(window[mid:]))
    left_max = float(np.max(window[:mid]))
    right_max = float(np.max(window[mid:]))
    if abs(left_min - right_min) / max(left_min, 1e-6) < 0.03 and close[-1] > np.mean(window):
        patterns.append("疑似双底")
    if abs(left_max - right_max) / max(left_max, 1e-6) < 0.03 and close[-1] < np.mean(window):
        patterns.append("疑似双顶")

    recent_high = high[-20:]
    recent_low = low[-20:]
    if np.ptp(recent_high) / np.mean(recent_high) < 0.04 and np.ptp(recent_low) / np.mean(recent_low) < 0.05:
        patterns.append("三角形收敛")

    if vol[-1] > np.mean(vol[-20:]) * 1.8 and close[-1] > close[-5]:
        patterns.append("放量突破")

    return patterns


def _f(v: float) -> float:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0.0
    return round(float(v), 3)