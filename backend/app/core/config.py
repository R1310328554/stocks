"""应用配置：数据源凭证通过环境变量注入，默认走演示数据。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "智选投"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'stocks.db'}"

    # 数据源：有密钥则优先真实接口，否则自动降级为演示数据
    data_mode: str = "auto"  # auto | live | demo
    tushare_token: str = ""
    eastmoney_cookie: str = ""
    cninfo_cookie: str = ""

    # 选股参数
    default_universe_size: int = 80
    top_n_picks: int = 20
    factor_lookback_days: int = 120

    # 调度
    enable_scheduler: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_live_data(self) -> bool:
        if self.data_mode == "live":
            return True
        if self.data_mode == "demo":
            return False
        return bool(self.tushare_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()