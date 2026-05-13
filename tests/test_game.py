import unittest

from longyan_mj.bot import BasicBot, ShantenBot
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
                ShantenBot(name="强", use_effective_draws=True),
            ],
        )
        self.assertEqual(["弱", "中", "强"], [bot.name for bot in game.bots])


if __name__ == "__main__":
    unittest.main()
