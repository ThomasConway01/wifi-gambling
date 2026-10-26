"""
Unit tests for European Roulette betting calculations, odds, and edge cases.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from app.roulette import (
    evaluate_bet,
    get_number_color,
    format_hours_minutes,
    RED_NUMBERS,
    BLACK_NUMBERS,
    ROULETTE_ORDER
)
from app.models import BetItem

class TestBettingMath(unittest.TestCase):

    def test_wheel_order_and_counts(self):
        self.assertEqual(len(ROULETTE_ORDER), 37)
        self.assertEqual(len(set(ROULETTE_ORDER)), 37)
        self.assertEqual(len(RED_NUMBERS), 18)
        self.assertEqual(len(BLACK_NUMBERS), 18)
        self.assertEqual(get_number_color(0), "green")

    def test_red_black_evaluations(self):
        # Bet 10h on Red
        bet_red = BetItem(bet_type="color", bet_selection="red", wager_seconds=36000, wager_hours=10.0)
        # Winning number 14 (Red)
        res_win = evaluate_bet(bet_red, 14)
        self.assertTrue(res_win.is_win)
        self.assertEqual(res_win.profit_hours, 10.0)
        self.assertEqual(res_win.total_returned_hours, 20.0)

        # Winning number 2 (Black)
        res_lose = evaluate_bet(bet_red, 2)
        self.assertFalse(res_lose.is_win)
        self.assertEqual(res_lose.profit_hours, -10.0)
        self.assertEqual(res_lose.total_returned_hours, 0.0)

        # Winning number 0 (Green)
        res_zero = evaluate_bet(bet_red, 0)
        self.assertFalse(res_zero.is_win)
        self.assertEqual(res_zero.profit_hours, -10.0)

    def test_even_odd_evaluations(self):
        bet_even = BetItem(bet_type="parity", bet_selection="even", wager_seconds=7200, wager_hours=2.0)
        self.assertTrue(evaluate_bet(bet_even, 8).is_win)
        self.assertFalse(evaluate_bet(bet_even, 7).is_win)
        self.assertFalse(evaluate_bet(bet_even, 0).is_win)  # 0 is neither even nor odd in casino rules

    def test_dozens_evaluations(self):
        # 1st 12 (1-12) pays 2:1 (triple total return)
        bet_dozen = BetItem(bet_type="dozen", bet_selection="1st12", wager_seconds=3600, wager_hours=1.0)
        res_win = evaluate_bet(bet_dozen, 5)
        self.assertTrue(res_win.is_win)
        self.assertEqual(res_win.profit_hours, 2.0)
        self.assertEqual(res_win.total_returned_hours, 3.0)

        res_loss = evaluate_bet(bet_dozen, 15)
        self.assertFalse(res_loss.is_win)

    def test_columns_evaluations(self):
        # Column 1: 1, 4, 7, 10, ...
        bet_col = BetItem(bet_type="column", bet_selection="col1", wager_seconds=3600, wager_hours=1.0)
        self.assertTrue(evaluate_bet(bet_col, 4).is_win)
        self.assertFalse(evaluate_bet(bet_col, 5).is_win)

    def test_straight_up_jackpot(self):
        # Straight up on lucky number 7 pays 35:1
        bet_seven = BetItem(bet_type="straight", bet_selection="7", wager_seconds=3600, wager_hours=1.0)
        res_win = evaluate_bet(bet_seven, 7)
        self.assertTrue(res_win.is_win)
        self.assertEqual(res_win.profit_hours, 35.0)
        self.assertEqual(res_win.total_returned_hours, 36.0)

        res_lose = evaluate_bet(bet_seven, 8)
        self.assertFalse(res_lose.is_win)

    def test_formatting(self):
        self.assertEqual(format_hours_minutes(168 * 3600), "168h 00m")
        self.assertEqual(format_hours_minutes(90 * 60), "1h 30m")
        self.assertEqual(format_hours_minutes(0), "0h 00m")

if __name__ == "__main__":
    unittest.main()
