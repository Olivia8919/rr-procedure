from settings import settings


def calc_coins(tenure_months: int) -> int:
    """按司龄月份计算分配的 Coin 数：每 1 月 = 1 Coin，上限 20"""
    return min(tenure_months, settings.MAX_COINS_ALLOCATED)


def validate_transfer(
    allocated: int,
    given: int,
    target_given: int,
    amount: int,
    from_user: str,
    to_user: str,
) -> str | None:
    """返回 None 表示通过，否则返回中文错误信息"""
    if from_user == to_user:
        return "不能转赠给自己"
    if amount < 1:
        return "转赠数量至少为 1"
    if given + amount > allocated:
        return f"余额不足，你还有 {allocated - given} 个 Coin 可赠"
    if target_given + amount > settings.MAX_COINS_PER_PAIR:
        remaining = settings.MAX_COINS_PER_PAIR - target_given
        return f"给同一人的赠予上限为 {settings.MAX_COINS_PER_PAIR}，你还可赠 {max(0, remaining)} 个"
    return None
