import unittest

from longyan_mj.bot import AbilityConfig, BasicBot, ShantenBot, build_bot_from_abilities
from longyan_mj.evaluator import WinResult
from longyan_mj.game import MahjongGame
from longyan_mj.tiles import build_wall


class GameTest(unittest.TestCase):
    def test_wall_has_136_tiles(self):
        self.assertEqual(136, len(build_wall()))

    def test_start_round_deals_and_reveals_gold(self):
        game = MahjongGame(seed=7)
        game.start_round()
        hand_sizes = [len(player.hand) for player in game.players]
        self.assertEqual([14, 13, 13, 13], hand_sizes)
        self.assertIsNotNone(game.gold_tile)
        self.assertEqual(82, len(game.wall))

    def test_gold_tile_cannot_be_ponged(self):
        game = MahjongGame(seed=1)
        player = game.players[0]
        player.hand = ["M1", "M1", "M2"]
        self.assertFalse(player.can_pong("M1", "M1"))
        self.assertTrue(player.can_pong("M1", "WHITE"))

    def test_bot_avoids_discarding_gold_when_possible(self):
        bot = BasicBot()
        discard = bot.choose_discard(["WHITE", "M1", "M1", "EAST"], "WHITE")
        self.assertNotEqual("WHITE", discard)

    def test_all_bot_round_finishes(self):
        game = MahjongGame(seed=3)
        for player in game.players:
            player.is_human = False
        result = game.play(input_func=lambda prompt: "", output_func=lambda message: None)
        self.assertIn(result.reason, ("win", "draw"))
        if result.reason == "win":
            self.assertIsNotNone(result.score)

    def test_game_can_use_configured_bot_policies(self):
        game = MahjongGame(
            seed=2,
            bot_policies=[
                BasicBot(name="弱"),
                ShantenBot(name="中", use_effective_draws=False),
                build_bot_from_abilities("强", AbilityConfig.expert()),
            ],
        )
        self.assertEqual(["弱", "中", "强"], [bot.name for bot in game.bots])

    def test_bot_context_includes_discards_gold_and_melds(self):
        game = MahjongGame(seed=2)
        game.start_round()
        game.discards_by_player[1].append("M1")
        game.discards.append("M1")
        game.players[2].melds.append(type("MeldStub", (), {"tiles": ["T2", "T2", "T2"]})())
        context = game._bot_context(3)
        self.assertEqual(1, context.visible_counts["M1"])
        self.assertEqual(3, context.visible_counts["T2"])
        self.assertEqual(1, context.visible_counts[game.gold_tile])

    def test_finish_single_you_scores_as_single_you(self):
        game = MahjongGame(seed=1)
        game.start_round()
        player = game.players[0]
        player.youjin_level = 1
        result = game._finish_win(
            player,
            WinResult("single_you", "单游", 5),
            output_func=lambda message: None,
            discard_count=3,
            draw_count=2,
            pong_count=0,
        )
        self.assertEqual("single_you", result.win.kind)
        self.assertEqual("单游", result.score.win_label)
        self.assertEqual(5, result.score.multiplier)
        self.assertEqual(0, player.youjin_level)

    def test_finish_double_you_scores_as_double_you(self):
        game = MahjongGame(seed=1)
        game.start_round()
        player = game.players[0]
        player.youjin_level = 2
        result = game._finish_win(
            player,
            WinResult("double_you", "双游", 10),
            output_func=lambda message: None,
            discard_count=3,
            draw_count=2,
            pong_count=0,
        )
        self.assertEqual("double_you", result.win.kind)
        self.assertEqual("双游", result.score.win_label)
        self.assertEqual(10, result.score.multiplier)
        self.assertEqual(0, player.youjin_level)


if __name__ == "__main__":
    unittest.main()
