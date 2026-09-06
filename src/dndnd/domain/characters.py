POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27


def point_buy_total(scores: dict[str, int]) -> int:
    return sum(POINT_BUY_COSTS.get(score, 999) for score in scores.values())


def proficiency_bonus_for_level(level: int) -> int:
    return 2 + max(0, (level - 1) // 4)
