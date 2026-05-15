import unittest

from longyan_mj.evaluator import WinResult
from longyan_mj.scoring import DEFAULT_WIN_RULES, score_kong, score_rob_kong, score_self_draw


class ScoringTest(unittest.TestCase):
    def test_dealer_self_draw_doubles_all_losers(self):
        score = score_self_draw(winner=0, dealer=0, win=WinResult("standard", "自摸", 1))
        self.assertEqual([6, -2, -2, -2], score.payments)
        self.assertEqual(1, score.multiplier)

    def test_non_dealer_self_draw_dealer_pays_double(self):
        score = score_self_draw(winner=2, dealer=0, win=WinResult("seven_pairs", "七对", 3))
        self.assertEqual([-6, -3, 12, -3], score.payments)
        self.assertEqual(3, score.multiplier)
        self.assertEqual("七对自摸", score.win_label)

    def test_supported_win_score_rules(self):
        self.assertEqual(3, DEFAULT_WIN_RULES["three_gold"].multiplier)
        self.assertEqual(4, DEFAULT_WIN_RULES["qiang_jin"].multiplier)
        self.assertEqual(2, DEFAULT_WIN_RULES["kong_bloom"].multiplier)
        self.assertEqual(20, DEFAULT_WIN_RULES["thirteen_orphans"].multiplier)
        self.assertEqual(5, DEFAULT_WIN_RULES["single_you"].multiplier)
        self.assertEqual(10, DEFAULT_WIN_RULES["double_you"].multiplier)
        self.assertEqual(24, DEFAULT_WIN_RULES["seven_pairs_triple_you"].multiplier)

    def test_kong_scores_use_dealer_multiplier(self):
        exposed = score_kong("added", kong_player=2, dealer=0)
        self.assertEqual([-2, -1, 4, -1], exposed.payments)

        concealed = score_kong("concealed", kong_player=0, dealer=0)
        self.assertEqual([12, -4, -4, -4], concealed.payments)

    def test_discarded_exposed_kong_is_paid_by_source(self):
        score = score_kong("exposed", kong_player=2, dealer=0, source_player=1)
        self.assertEqual([0, -4, 4, 0], score.payments)

    def test_rob_kong_is_paid_by_robbed_player(self):
        score = score_rob_kong(
            winner=2,
            robbed_player=1,
            dealer=0,
            win=WinResult("standard", "自摸", 1),
        )
        self.assertEqual([0, -4, 4, 0], score.payments)
        self.assertEqual("抢杠胡", score.win_label)


if __name__ == "__main__":
    unittest.main()
