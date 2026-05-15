import unittest

from collections import Counter

from longyan_mj.bot import (
    ABILITY_DEFENSE,
    ABILITY_EFFECTIVE_DRAWS,
    ABILITY_GOLD_STRATEGY,
    ABILITY_HAND_VALUE,
    ABILITY_DANGER_REFINED,
    ABILITY_EXPLANATION,
    ABILITY_KONG_EV,
    ABILITY_MONTE_CARLO,
    ABILITY_OPPONENT_TENPAI,
    ABILITY_PONG_EV,
    ABILITY_REMAINING_TILES,
    ABILITY_SHANTEN,
    ABILITY_STYLE_CONTROL,
    ABILITY_YOUJIN_STRATEGY,
    AbilityConfig,
    BotStyle,
    BotContext,
    ConfigurableBot,
    ExpertBot,
    ShantenBot,
    build_bot_from_abilities,
    default_bot_policies,
)
from longyan_mj.shanten import analyze_discards, effective_draws, estimate_shanten
from longyan_mj.tiles import FLOWERS


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

    def test_effective_draws_do_not_include_flowers(self):
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
        self.assertTrue(set(draws).isdisjoint(FLOWERS))

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
        self.assertIn("专家", bots[2].name)

    def test_ability_config_can_be_built_from_purchased_ids(self):
        abilities = AbilityConfig.from_ids(
            [
                ABILITY_SHANTEN,
                ABILITY_EFFECTIVE_DRAWS,
                ABILITY_REMAINING_TILES,
                ABILITY_HAND_VALUE,
                ABILITY_PONG_EV,
                ABILITY_DEFENSE,
                ABILITY_GOLD_STRATEGY,
                ABILITY_STYLE_CONTROL,
                ABILITY_OPPONENT_TENPAI,
                ABILITY_DANGER_REFINED,
                ABILITY_KONG_EV,
                ABILITY_YOUJIN_STRATEGY,
                ABILITY_MONTE_CARLO,
                ABILITY_EXPLANATION,
            ]
        )
        self.assertTrue(abilities.shanten)
        self.assertTrue(abilities.remaining_tiles)
        self.assertIn(ABILITY_DEFENSE, abilities.enabled_ids())
        self.assertTrue(abilities.explanation)

    def test_bot_factory_uses_ability_config(self):
        basic = build_bot_from_abilities("basic", AbilityConfig.basic())
        shanten = build_bot_from_abilities("shanten", AbilityConfig.shanten_only())
        expert = build_bot_from_abilities("expert", AbilityConfig.expert())
        self.assertEqual("BasicBot", basic.__class__.__name__)
        self.assertEqual("ShantenBot", shanten.__class__.__name__)
        self.assertEqual("ConfigurableBot", expert.__class__.__name__)

    def test_context_counts_remaining_visible_tiles(self):
        context = BotContext(
            current_player=2,
            dealer=0,
            wall_remaining=50,
            visible_counts=Counter({"M1": 2, "WHITE": 1}),
            discards_by_player=((), ("M1",), (), ()),
            melds_by_player=((), (), (), ()),
        )
        self.assertEqual(1, context.remaining_count("M1", ["M1"]))
        self.assertEqual(3, context.remaining_effective_count(["M1", "WHITE"], ["M1", "WHITE"]))

    def test_expert_bot_values_remaining_effective_tiles(self):
        bot = ExpertBot()
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
        context = BotContext(
            current_player=3,
            dealer=0,
            wall_remaining=40,
            visible_counts=Counter({"S6": 4, "S9": 4, "WHITE": 4}),
            discards_by_player=((), (), (), ()),
            melds_by_player=((), (), (), ()),
        )
        analyses = {analysis.tile: analysis for analysis in analyze_discards(hand, "WHITE")}
        next_hand = hand[:]
        next_hand.remove("EAST")
        self.assertEqual(0, bot._remaining_effective_count(analyses["EAST"], next_hand, "WHITE", 0, context))

    def test_expert_bot_can_decline_bad_pong(self):
        bot = ExpertBot()
        hand = [
            "M1",
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
        ]
        self.assertFalse(bot.wants_pong(hand, "M1", "WHITE"))

    def test_configurable_bot_can_enable_gold_strategy(self):
        bot = ConfigurableBot(
            abilities=AbilityConfig(shanten=True, effective_draws=True, gold_strategy=True)
        )
        hand = [
            "WHITE",
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
            "EAST",
        ]
        self.assertNotEqual("WHITE", bot.choose_discard(hand, "WHITE"))

    def test_refined_danger_uses_opponent_tenpai_pressure(self):
        bot = ConfigurableBot(
            abilities=AbilityConfig(
                shanten=True,
                defense=True,
                opponent_tenpai=True,
                danger_refined=True,
            )
        )
        context = BotContext(
            current_player=2,
            dealer=0,
            wall_remaining=20,
            visible_counts=Counter(),
            discards_by_player=(("M1",) * 12, (), (), ()),
            melds_by_player=((), (), (), ()),
        )
        danger = bot._risk_score("M5", ["M5"], context)
        self.assertGreater(danger, 0)

    def test_kong_and_youjin_values_are_configurable(self):
        bot = ConfigurableBot(abilities=AbilityConfig(kong_ev=True, youjin_strategy=True))
        self.assertGreater(bot._kong_value(["M1", "M1", "M1", "M1"], "WHITE"), 0)
        self.assertGreater(bot._youjin_value(["WHITE", "WHITE", "M1", "M1"], "WHITE"), 0)

    def test_monte_carlo_score_uses_remaining_effective_count(self):
        bot = ConfigurableBot(abilities=AbilityConfig(shanten=True, monte_carlo=True))
        context = BotContext(
            current_player=0,
            dealer=0,
            wall_remaining=40,
            visible_counts=Counter({"S6": 3}),
            discards_by_player=((), (), (), ()),
            melds_by_player=((), (), (), ()),
        )
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
        analysis = {item.tile: item for item in analyze_discards(hand, "WHITE")}["EAST"]
        next_hand = hand[:]
        next_hand.remove("EAST")
        self.assertGreater(bot._monte_carlo_score(analysis, next_hand, context), 0)

    def test_explanation_ability_returns_reason_text(self):
        bot = ConfigurableBot(
            abilities=AbilityConfig(
                shanten=True,
                effective_draws=True,
                remaining_tiles=True,
                defense=True,
                explanation=True,
            ),
            style=BotStyle.defensive(),
        )
        context = BotContext(
            current_player=0,
            dealer=0,
            wall_remaining=40,
            visible_counts=Counter(),
            discards_by_player=((), (), (), ()),
            melds_by_player=((), (), (), ()),
        )
        text = bot.explain_discard(
            [
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
            ],
            "WHITE",
            context=context,
        )
        self.assertIn("建议打出", text)
        self.assertIn("向听", text)


if __name__ == "__main__":
    unittest.main()
