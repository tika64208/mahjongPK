import unittest

from longyan_mj.evaluator import evaluate_win, is_seven_pairs, is_standard_win, is_thirteen_orphans
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


if __name__ == "__main__":
    unittest.main()
