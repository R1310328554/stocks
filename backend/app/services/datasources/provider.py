"""统一数据提供层：Tushare / akshare 优先，失败或无密钥时降级演示数据."""

from __future__ import annotations

import logging
from datetime import date, datetime
from functools import lru_cache

import pandas as pd

from app.core.config import get_settings
from app.services.datasources import demo_data

logger = logging.getLogger(__name__)


class DataProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._tushare = None
        self.source_name = "demo"
        if self.settings.use_live_data:
            self._init_live()

    def _init_live(self) -> None:
        try:
            import tushare as ts

            if not self.settings.tushare_token:
                logger.warning("未配置 TUSHARE_TOKEN，使用演示数据")
                return
            ts.set_token(self.settings.tushare_token)
            self._tushare = ts.pro_api()
            self.source_name = "tushare"
            logger.info("Tushare Pro 已就绪")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tushare 初始化失败，降级演示数据: %s", exc)
            self._tushare = None
            self.source_name = "demo"

    def list_stocks(self, limit: int | None = None) -> list[dict]:
        if self._tushare is not None:
            try:
                df = self._tushare.stock_basic(
                    exchange="",
                    list_status="L",
                    fields="ts_code,symbol,name,industry,market,list_date",
                )
                rows = df.fillna("").to_dict(orient="records")
                return rows[: limit or self.settings.default_universe_size]
            except Exception as exc:  # noqa: BLE001
                logger.warning("拉取股票列表失败，使用演示池: %s", exc)
        rows = demo_data.list_stocks()
        return rows[: limit or len(rows)]

    def get_daily_bars(self, ts_code: str, days: int = 180) -> pd.DataFrame:
        if self._tushare is not None:
            try:
                end = date.today().strftime("%Y%m%d")
                start = (date.today().fromordinal(date.today().toordinal() - days * 2)).strftime(
                    "%Y%m%d"
                )
                df = self._tushare.daily(ts_code=ts_code, start_date=start, end_date=end)
                if df is not None and not df.empty:
                    df = df.sort_values("trade_date")
                    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
                    return df.tail(days).reset_index(drop=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("日线拉取失败 %s: %s", ts_code, exc)
        return demo_data.generate_daily_bars(ts_code, days=days)

    def get_fundamentals(self, ts_code: str) -> dict:
        if self._tushare is not None:
            try:
                # 估值 + 财务指标拼接；权限不足时自动降级
                daily_basic = self._tushare.daily_basic(
                    ts_code=ts_code,
                    trade_date=date.today().strftime("%Y%m%d"),
                    fields="ts_code,pe,pb,ps,turnover_rate,dv_ratio",
                )
                fina = self._tushare.fina_indicator(
                    ts_code=ts_code,
                    fields="ts_code,roe,roa,grossprofit_margin,netprofit_margin,debt_to_assets,or_yoy,netprofit_yoy,basic_eps_yoy",
                )
                snap = demo_data.fundamental_snapshot(ts_code)
                if daily_basic is not None and not daily_basic.empty:
                    row = daily_basic.iloc[0]
                    snap.update(
                        {
                            "pe": float(row.get("pe") or snap["pe"]),
                            "pb": float(row.get("pb") or snap["pb"]),
                            "ps": float(row.get("ps") or snap["ps"]),
                            "turnover": float(row.get("turnover_rate") or snap["turnover"]),
                            "dividend_yield": float(row.get("dv_ratio") or snap["dividend_yield"]),
                        }
                    )
                if fina is not None and not fina.empty:
                    row = fina.iloc[0]
                    snap.update(
                        {
                            "roe": float(row.get("roe") or snap["roe"]),
                            "roa": float(row.get("roa") or snap["roa"]),
                            "gross_margin": float(row.get("grossprofit_margin") or snap["gross_margin"]),
                            "net_margin": float(row.get("netprofit_margin") or snap["net_margin"]),
                            "debt_ratio": float(row.get("debt_to_assets") or snap["debt_ratio"]),
                            "revenue_growth": float(row.get("or_yoy") or snap["revenue_growth"]),
                            "profit_growth": float(row.get("netprofit_yoy") or snap["profit_growth"]),
                            "eps_growth": float(row.get("basic_eps_yoy") or snap["eps_growth"]),
                        }
                    )
                return snap
            except Exception as exc:  # noqa: BLE001
                logger.warning("基本面拉取失败 %s: %s", ts_code, exc)
        return demo_data.fundamental_snapshot(ts_code)

    def get_market_overview(self) -> dict:
        overview = demo_data.market_overview()
        overview["data_source"] = self.source_name
        if self._tushare is not None:
            try:
                # 指数日线作为增强；失败不影响演示
                idx = self._tushare.index_daily(ts_code="000001.SH", limit=1)
                if idx is not None and not idx.empty:
                    overview["index_summary"][0] = {
                        "name": "上证指数",
                        "close": float(idx.iloc[0]["close"]),
                        "pct_chg": float(idx.iloc[0]["pct_chg"]),
                    }
                    overview["data_source"] = "tushare"
            except Exception as exc:  # noqa: BLE001
                logger.warning("指数概览增强失败: %s", exc)
        return overview

    def get_news(self, limit: int = 20) -> list[dict]:
        # 新闻源多样且鉴权复杂，MVP 统一封装演示流；live 模式下保留同结构便于替换
        return demo_data.news_feed(limit=limit)

    def get_alerts(self, limit: int = 15) -> list[dict]:
        return demo_data.alerts(limit=limit)

    def resolve_name(self, ts_code: str) -> dict:
        for s in self.list_stocks():
            if s["ts_code"] == ts_code or s["symbol"] == ts_code:
                return s
        return {
            "ts_code": ts_code if "." in ts_code else f"{ts_code}.SH",
            "symbol": ts_code.split(".")[0],
            "name": ts_code,
            "industry": "未知",
            "market": "",
        }


@lru_cache(maxsize=1)
def get_data_provider() -> DataProvider:
    return DataProvider()