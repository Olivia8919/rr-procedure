import aiosqlite
import os
from settings import settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        os.makedirs(os.path.dirname(settings.DB_PATH) or ".", exist_ok=True)
        _db = await aiosqlite.connect(settings.DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id   TEXT NOT NULL,
                from_user  TEXT NOT NULL,
                to_user    TEXT NOT NULL,
                coins      INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tx_round_from
                ON transactions(round_id, from_user);
            CREATE INDEX IF NOT EXISTS idx_tx_round_from_to
                ON transactions(round_id, from_user, to_user);
        """)
        await _db.commit()
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
