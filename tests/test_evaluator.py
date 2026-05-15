import unittest

from longyan_mj.evaluator import (
    evaluate_qiangjin,
    evaluate_win,
    find_youjin_discard,
    is_seven_pairs,
    is_standard_win,
    is_thirteen_orphans,
)
from longyan_mj.tiles import is_numbered


class EvaluatorTest(unittest.TestCase):
    def test_honors_are_not_numbered_tiles(self):
        self.assertFalse(is_numbered("SOUTH"))
        self.assertTrue(is_numbered("S1"))

    def test_standard_win_without_gold(self):
        tiles = [
            "M1",
            "M2",
            "M3",
            "M2",
            "M3",
            "M4",
            "T3",
            "T4",
            "T5",
            "S7",
            "S8",
            "S9",
            "RED",
            "RED",
        ]
        self.assertTrue(is_standard_win(tiles, "WHITE"))

    def test_standard_win_with_gold_as_wildcard(self):
        tiles = [
            "M1",
            "M2",
            "WHITE",
            "M2",
            "M3",
            "M4",
            "T3",
            "T4",
            "T5",
            "S7",
            "S8",
            "S9",
            "RED",
            "RED",
        ]
        self.assertTrue(is_standard_win(tiles, "WHITE"))

    def test_seven_pairs_with_gold(self):
        tiles = [
            "M1",
            "M1",
            "M2",
            "M2",
            "M3",
            "M3",
            "T4",
            "T4",
            "S5",
            "S5",
            "RED",
            "RED",
            "GREEN",
            "WHITE",
        ]
        self.assertTrue(is_seven_pairs(tiles, "WHITE"))

    def test_thirteen_orphans_with_gold(self):
        tiles = [
            "M1",
            "M9",
            "T1",
            "T9",
            "S1",
            "S9",
            "EAST",
            "SOUTH",
            "WEST",
            "NORTH",
            "RED",
            "GREEN",
            "WHITE",
            "M1",
        ]
        self.assertTrue(is_thirteen_orphans(tiles, "WHITE"))

    def test_three_gold_has_priority(self):
        tiles = [
            "WHITE",
            "WHITE",
            "WHITE",
            "M2",
            "M3",
            "M4",
            "T3",
            "T4",
            "T5",
            "S7",
            "S8",
            "S9",
            "RED",
            "RED",
        ]
        win = evaluate_win(tiles, "WHITE")
        self.assertIsNotNone(win)
        self.assertEqual("three_gold", win.kind)

    def test_evaluate_qiangjin_for_idle_player(self):
        tiles = [
            "M1",
            "M2",
            "M3",
            "M4",
            "M5",
            "M6",
            "T2",
            "T3",
            "T4",
            "S7",
            "S8",
            "S9",
            "RED",
        ]
        win = evaluate_qiangjin(tiles, "WHITE")
        self.assertIsNotNone(win)
        self.assertEqual("qiang_jin", win.kind)

    def test_evaluate_qiangjin_for_dealer_after_one_discard(self):
        tiles = [
            "M1",
            "M2",
            "M3",
            "M4",
            "M5",
            "M6",
            "T2",
            "T3",
            "T4",
            "S7",
            "S8",
            "S9",
            "RED",
            "EAST",
        ]
        win = evaluate_qiangjin(tiles, "WHITE")
        self.assertIsNotNone(win)
        self.assertEqual("qiang_jin", win.kind)

    def test_find_youjin_discard(self):
        tiles = [
            "WHITE",
            "M1",
            "M2",
            "M3",
            "M4",
            "M5",
            "M6",
            "T2",
            "T3",
            "T4",
            "S7",
            "S8",
            "S9",
            "RED",
        ]
        self.assertEqual("RED", find_youjin_discard(tiles, "WHITE"))

    def test_find_youjin_discard_with_two_gold_open_hand(self):
        tiles = [
            "M4",
            "M5",
            "M6",
            "M7",
            "M9",
            "T3",
            "T4",
            "T5",
            "S9",
            "S9",
            "GREEN",
        ]
        self.assertEqual("GREEN", find_youjin_discard(tiles, "S9", open_melds=1))


if __name__ == "__main__":
    unittest.main()
