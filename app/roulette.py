"""
Roulette game mechanics, payouts, pocket configurations, and verification.
"""

import secrets
from typing import Dict, Any, List, Tuple
from app.models import BetItem, BetOutcome

ROULETTE_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5,
    24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

COL_1 = {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}
COL_2 = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}
COL_3 = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}

def get_number_color(num: int) -> str:
    if num == 0:
        return "green"
    return "red" if num in RED_NUMBERS else "black"

def spin_wheel() -> int:
    """True cryptographic random spin 0..36"""
    return secrets.randbelow(37)

def evaluate_bet(bet: BetItem, winning_number: int) -> BetOutcome:
    """
    Evaluates an individual bet against the winning roulette number.
    Returns BetOutcome with profit and payout.
    """
    b_type = bet.bet_type.lower()
    b_sel = str(bet.bet_selection).lower()
    wager = bet.wager_hours

    is_win = False
    payout_multiplier = 0.0  # Profit multiplier (e.g. 1.0 for 1:1, 2.0 for 2:1, 35.0 for straight up)

    if b_type == "color" or b_sel in ["red", "black"]:
        if b_sel == "red" and winning_number in RED_NUMBERS:
            is_win = True
            payout_multiplier = 1.0
        elif b_sel == "black" and winning_number in BLACK_NUMBERS:
            is_win = True
            payout_multiplier = 1.0

    elif b_type == "parity" or b_sel in ["even", "odd"]:
        if winning_number != 0:
            if b_sel == "even" and winning_number % 2 == 0:
                is_win = True
                payout_multiplier = 1.0
            elif b_sel == "odd" and winning_number % 2 == 1:
                is_win = True
                payout_multiplier = 1.0

    elif b_type == "range" or b_sel in ["low", "high", "1-18", "19-36"]:
        if winning_number != 0:
            if b_sel in ["low", "1-18"] and 1 <= winning_number <= 18:
                is_win = True
                payout_multiplier = 1.0
            elif b_sel in ["high", "19-36"] and 19 <= winning_number <= 36:
                is_win = True
                payout_multiplier = 1.0

    elif b_type == "dozen" or b_sel in ["1st12", "2nd12", "3rd12", "dozen_1", "dozen_2", "dozen_3"]:
        if b_sel in ["1st12", "dozen_1"] and 1 <= winning_number <= 12:
            is_win = True
            payout_multiplier = 2.0
        elif b_sel in ["2nd12", "dozen_2"] and 13 <= winning_number <= 24:
            is_win = True
            payout_multiplier = 2.0
        elif b_sel in ["3rd12", "dozen_3"] and 25 <= winning_number <= 36:
            is_win = True
            payout_multiplier = 2.0

    elif b_type == "column" or b_sel in ["col1", "col2", "col3", "col_1", "col_2", "col_3"]:
        if b_sel in ["col1", "col_1"] and winning_number in COL_1:
            is_win = True
            payout_multiplier = 2.0
        elif b_sel in ["col2", "col_2"] and winning_number in COL_2:
            is_win = True
            payout_multiplier = 2.0
        elif b_sel in ["col3", "col_3"] and winning_number in COL_3:
            is_win = True
            payout_multiplier = 2.0

    elif b_type in ["straight", "number"]:
        try:
            target_num = int(b_sel)
            if target_num == winning_number:
                is_win = True
                payout_multiplier = 35.0  # 35 to 1 payout
        except ValueError:
            pass

    if is_win:
        profit_hours = round(wager * payout_multiplier, 4)
        total_returned_hours = round(wager + profit_hours, 4)
    else:
        profit_hours = round(-wager, 4)
        total_returned_hours = 0.0

    return BetOutcome(
        bet_type=bet.bet_type,
        bet_selection=bet.bet_selection,
        wager_hours=wager,
        is_win=is_win,
        payout_multiplier=payout_multiplier,
        profit_hours=profit_hours,
        total_returned_hours=total_returned_hours
    )

def format_hours_minutes(seconds: float) -> str:
    """Converts seconds into friendly '168h 00m' or '0h 00m' format."""
    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes:02d}m"
