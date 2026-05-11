import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    # 飞书应用
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_API_BASE: str = "https://open.feishu.cn/open-apis"

    # 飞书多维表格 ID（员工花名册为现有表格）
    BITABLE_APP_TOKEN: str = os.getenv("BITABLE_APP_TOKEN", "")
    EMPLOYEES_TABLE_ID: str = os.getenv("EMPLOYEES_TABLE_ID", "")
    ROUNDS_TABLE_ID: str = os.getenv("ROUNDS_TABLE_ID", "")
    BALANCES_TABLE_ID: str = os.getenv("BALANCES_TABLE_ID", "")
    STARWALL_TABLE_ID: str = os.getenv("STARWALL_TABLE_ID", "")

    # SQLite
    DB_PATH: str = os.getenv("DB_PATH", "rr.db")

    # 权限
    SUPER_ADMINS: list[str] = field(default_factory=lambda: [
        # 填写飞书 open_id
    ])

    # Coin 分配规则：每 1 个月司龄 = 1 Coin，上限 20
    MAX_COINS_ALLOCATED: int = 20

    # Session
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "change-me-in-production")
    SESSION_MAX_AGE: int = 86400 * 7  # 7 天

    # 单人给同一对象的上限
    MAX_COINS_PER_PAIR: int = 3

settings = Settings()
