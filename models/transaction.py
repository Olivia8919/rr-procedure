from database import get_db


async def add_transaction(round_id: str, from_user: str, to_user: str, coins: int):
    db = await get_db()
    await db.execute(
        "INSERT INTO transactions (round_id, from_user, to_user, coins) VALUES (?, ?, ?, ?)",
        (round_id, from_user, to_user, coins),
    )
    await db.commit()


async def get_given_to(round_id: str, from_user: str, to_user: str) -> int:
    """某人对另一人在本轮已转出的 Coin 总数"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COALESCE(SUM(coins), 0) FROM transactions "
        "WHERE round_id = ? AND from_user = ? AND to_user = ?",
        (round_id, from_user, to_user),
    )
    row = await cursor.fetchone()
    return row[0]


async def get_total_given(round_id: str, from_user: str) -> int:
    """某人在本轮已转出的 Coin 总数"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COALESCE(SUM(coins), 0) FROM transactions "
        "WHERE round_id = ? AND from_user = ?",
        (round_id, from_user),
    )
    row = await cursor.fetchone()
    return row[0]


async def get_transactions_by_round(round_id: str, search: str = None) -> list[dict]:
    """超管查询交易明细，支持按姓名筛选"""
    db = await get_db()
    if search:
        rows = await db.execute(
            "SELECT * FROM transactions WHERE round_id = ? AND "
            "(from_user LIKE ? OR to_user LIKE ?) ORDER BY created_at DESC",
            (round_id, f"%{search}%", f"%{search}%"),
        )
    else:
        rows = await db.execute(
            "SELECT * FROM transactions WHERE round_id = ? ORDER BY created_at DESC",
            (round_id,),
        )
    result = await rows.fetchall()
    return [dict(r) for r in result]
