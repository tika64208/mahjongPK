import unittest

from longyan_mj.bot import ShantenBot, default_bot_policies
from longyan_mj.shanten import analyze_discards, effective_draws, estimate_shanten


class ShantenTest(unittest.TestCase):
    def test_effective_draws_detect_tenpai(self):
        hand = [
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
            "RED",
            "RED",
        ]
        draws = effective_draws(hand, "WHITE")
        self.assertIn("S6", draws)
        self.assertIn("S9", draws)
        self.assertEqual(0, estimate_shanten(hand, "WHITE"))

    def test_analyze_discards_prefers_tenpai_discard(self):
        hand = [
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
            "RED",
            "RED",
            "EAST",
        ]
        analyses = {analysis.tile: analysis for analysis in analyze_discards(hand, "WHITE")}
        self.assertEqual(0, analyses["EAST"].shanten)
        self.assertGreater(analyses["EAST"].effective_draw_count, 0)

    def test_shanten_bot_discards_isolated_tile_to_keep_tenpai(self):
        bot = ShantenBot()
        hand = [
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
            "RED",
            "RED",
            "EAST",
        ]
        self.assertEqual("EAST", bot.choose_discard(hand, "WHITE"))

    def test_default_bots_have_different_abilities(self):
        bots = default_bot_policies()
        self.assertEqual(3, len(bots))
        self.assertNotEqual(bots[0].name, bots[1].name)
        self.assertIn("进张", bots[2].name)


if __name__ == "__main__":
    unittest.main()

