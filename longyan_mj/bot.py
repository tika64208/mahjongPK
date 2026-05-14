"""Bot policies and configurable purchasable abilities."""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Sequence

from .shanten import DiscardAnalysis, analyze_discards, effective_draws, estimate_shanten
from .tiles import HONORS, TERMINALS_AND_HONORS, TILE_INDEX, is_numbered, tile_number

ABILITY_BASIC_TILE_EFFICIENCY = "basic_tile_efficiency"
ABILITY_SHANTEN = "shanten"
ABILITY_EFFECTIVE_DRAWS = "effective_draws"
ABILITY_REMAINING_TILES = "remaining_tiles"
ABILITY_HAND_VALUE = "hand_value"
ABILITY_PONG_EV = "pong_ev"
ABILITY_DEFENSE = "defense"
ABILITY_GOLD_STRATEGY = "gold_strategy"
ABILITY_STYLE_CONTROL = "style_control"
ABILITY_OPPONENT_TENPAI = "opponent_tenpai"
ABILITY_DANGER_REFINED = "danger_refined"
ABILITY_KONG_EV = "kong_ev"
ABILITY_YOUJIN_STRATEGY = "youjin_strategy"
ABILITY_MONTE_CARLO = "monte_carlo"
ABILITY_EXPLANATION = "explanation"


class BotPolicy(Protocol):
    name: str

    def choose_discard(
        self,
        hand: List[str],
        gold_tile: str,
        open_melds: int = 0,
        context: Optional["BotContext"] = None,
    ) -> str:
        ...

    def wants_pong(
        self,
        hand: List[str],
        tile: str,
        gold_tile: str,
        open_melds: int = 0,
        context: Optional["BotContext"] = None,
    ) -> bool:
        ...


@dataclass(frozen=True)
class BotStyle:
    """Decision style multipliers for configurable bots."""

    name: str = "balanced"
    attack_weight: float = 1.0
    value_weight: float = 1.0
    defense_weight: float = 1.0
    gold_weight: float = 1.0

    @classmethod
    def aggressive(cls) -> "BotStyle":
        return cls("aggressive", attack_weight=1.3, value_weight=1.1, defense_weight=0.6)

    @classmethod
    def defensive(cls) -> "BotStyle":
        return cls("defensive", attack_weight=0.8, value_weight=0.9, defense_weight=1.6)

    @classmethod
    def value_seeking(cls) -> "BotStyle":
        return cls("value", attack_weight=0.9, value_weight=1.5, defense_weight=0.9, gold_weight=1.3)


@dataclass(frozen=True)
class AbilityConfig:
    """Configurable bot abilities.

    The shape is intentionally entitlement-friendly: a future account service can
    store purchased ability IDs and build this config at game start.
    """

    basic_tile_efficiency: bool = True
    shanten: bool = False
    effective_draws: bool = False
    remaining_tiles: bool = False
    hand_value: bool = False
    pong_ev: bool = False
    defense: bool = False
    gold_strategy: bool = False
    style_control: bool = False
    opponent_tenpai: bool = False
    danger_refined: bool = False
    kong_ev: bool = False
    youjin_strategy: bool = False
    monte_carlo: bool = False
    explanation: bool = False

    @classmethod
    def from_ids(cls, ability_ids: Sequence[str]) -> "AbilityConfig":
        abilities = set(ability_ids)
        return cls(
            basic_tile_efficiency=ABILITY_BASIC_TILE_EFFICIENCY in abilities or not abilities,
            shanten=ABILITY_SHANTEN in abilities,
            effective_draws=ABILITY_EFFECTIVE_DRAWS in abilities,
            remaining_tiles=ABILITY_REMAINING_TILES in abilities,
            hand_value=ABILITY_HAND_VALUE in abilities,
            pong_ev=ABILITY_PONG_EV in abilities,
            defense=ABILITY_DEFENSE in abilities,
            gold_strategy=ABILITY_GOLD_STRATEGY in abilities,
            style_control=ABILITY_STYLE_CONTROL in abilities,
            opponent_tenpai=ABILITY_OPPONENT_TENPAI in abilities,
            danger_refined=ABILITY_DANGER_REFINED in abilities,
            kong_ev=ABILITY_KONG_EV in abilities,
            youjin_strategy=ABILITY_YOUJIN_STRATEGY in abilities,
            monte_carlo=ABILITY_MONTE_CARLO in abilities,
            explanation=ABILITY_EXPLANATION in abilities,
        )

    def enabled_ids(self) -> List[str]:
        pairs = [
            (ABILITY_BASIC_TILE_EFFICIENCY, self.basic_tile_efficiency),
            (ABILITY_SHANTEN, self.shanten),
            (ABILITY_EFFECTIVE_DRAWS, self.effective_draws),
            (ABILITY_REMAINING_TILES, self.remaining_tiles),
            (ABILITY_HAND_VALUE, self.hand_value),
            (ABILITY_PONG_EV, self.pong_ev),
            (ABILITY_DEFENSE, self.defense),
            (ABILITY_GOLD_STRATEGY, self.gold_strategy),
            (ABILITY_STYLE_CONTROL, self.style_control),
            (ABILITY_OPPONENT_TENPAI, self.opponent_tenpai),
            (ABILITY_DANGER_REFINED, self.danger_refined),
            (ABILITY_KONG_EV, self.kong_ev),
            (ABILITY_YOUJIN_STRATEGY, self.youjin_strategy),
            (ABILITY_MONTE_CARLO, self.monte_carlo),
            (ABILITY_EXPLANATION, self.explanation),
        ]
        return [ability_id for ability_id, enabled in pairs if enabled]

    @classmethod
    def basic(cls) -> "AbilityConfig":
        return cls()

    @classmethod
    def shanten_only(cls) -> "AbilityConfig":
        return cls(shanten=True)

    @classmethod
    def expert(cls) -> "AbilityConfig":
        return cls(
            shanten=True,
            effective_draws=True,
            remaining_tiles=True,
            hand_value=True,
            pong_ev=True,
            defense=True,
            gold_strategy=True,
            style_control=True,
            opponent_tenpai=True,
            danger_refined=True,
            kong_ev=True,
            youjin_strategy=True,
            monte_carlo=True,
            explanation=True,
        )


@dataclass(frozen=True)
class BotContext:
    """Visible table information available to a bot."""

    current_player: int
    dealer: int
    wall_remaining: int
    visible_counts: Counter
    discards_by_player: Sequence[Sequence[str]]
    melds_by_player: Sequence[Sequence[Sequence[str]]]

    def remaining_count(self, tile: str, own_hand: Sequence[str]) -> int:
        return max(0, 4 - self.visible_counts.get(tile, 0) - own_hand.count(tile))

    def remaining_effective_count(self, draws: Sequence[str], own_hand: Sequence[str]) -> int:
        return sum(self.remaining_count(tile, own_hand) for tile in draws)

    def opponent_pressure(self, player_index: int) -> float:
        if player_index == self.current_player:
            return 0.0
        discard_count = len(self.discards_by_player[player_index])
        meld_count = len(self.melds_by_player[player_index])
        pressure = 0.0
        if discard_count >= 12:
            pressure += 1.0
        elif discard_count >= 8:
            pressure += 0.5
        pressure += min(1.5, meld_count * 0.5)
        return pressure

    def opponent_tenpai_likelihood(self, player_index: int) -> float:
        if player_index == self.current_player:
            return 0.0
        discard_count = len(self.discards_by_player[player_index])
        meld_count = len(self.melds_by_player[player_index])
        likelihood = 0.0
        if discard_count >= 14:
            likelihood += 0.55
        elif discard_count >= 10:
            likelihood += 0.35
        elif discard_count >= 7:
            likelihood += 0.18
        likelihood += min(0.35, meld_count * 0.12)
        if self.wall_remaining <= 24:
            likelihood += 0.15
        return min(0.95, likelihood)


@dataclass
class BasicBot:
    """A conservative bot that keeps pairs, neighbors and gold tiles."""

    name: str = "基础机器人"

    def choose_discard(
        self,
        hand: List[str],
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> str:
        candidates = [tile for tile in hand if tile != gold_tile]
        if not candidates:
            return hand[0]
        counts = Counter(hand)
        return min(candidates, key=lambda tile: (self._keep_score(tile, counts), TILE_INDEX[tile]))

    def wants_pong(
        self,
        hand: List[str],
        tile: str,
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> bool:
        if tile == gold_tile or hand.count(tile) < 2:
            return False
        if tile in HONORS:
            return True
        return hand.count(tile) >= 2 and self._neighbor_count(hand, tile) == 0

    def _keep_score(self, tile: str, counts: Counter) -> int:
        score = 0
        if counts[tile] >= 2:
            score += 4
        if counts[tile] >= 3:
            score += 3
        if tile in HONORS:
            return score
        score += self._neighbor_count(list(counts.elements()), tile)
        return score

    def _neighbor_count(self, hand: List[str], tile: str) -> int:
        if not is_numbered(tile):
            return 0
        suit = tile[:1]
        number = tile_number(tile)
        neighbors = 0
        for offset in (-2, -1, 1, 2):
            next_number = number + offset
            if 1 <= next_number <= 9 and f"{suit}{next_number}" in hand:
                neighbors += 1
        return neighbors


@dataclass
class ShantenBot(BasicBot):
    """A stronger bot that chooses discards by shanten and effective draws."""

    name: str = "算牌机器人"
    use_effective_draws: bool = True
    allow_shanten_pong: bool = True

    def choose_discard(
        self,
        hand: List[str],
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> str:
        abilities = AbilityConfig(
            shanten=True,
            effective_draws=self.use_effective_draws,
            pong_ev=self.allow_shanten_pong,
        )
        return ConfigurableBot(name=self.name, abilities=abilities).choose_discard(
            hand, gold_tile, open_melds, context
        )

    def wants_pong(
        self,
        hand: List[str],
        tile: str,
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> bool:
        abilities = AbilityConfig(
            shanten=True,
            effective_draws=self.use_effective_draws,
            pong_ev=self.allow_shanten_pong,
        )
        return ConfigurableBot(name=self.name, abilities=abilities).wants_pong(
            hand, tile, gold_tile, open_melds, context
        )


@dataclass
class ConfigurableBot(BasicBot):
    """A bot assembled from purchasable abilities."""

    name: str = "可配置机器人"
    abilities: AbilityConfig = field(default_factory=AbilityConfig.basic)
    style: BotStyle = field(default_factory=BotStyle)

    def choose_discard(
        self,
        hand: List[str],
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> str:
        if not self.abilities.shanten:
            return super().choose_discard(hand, gold_tile, open_melds, context)

        analyses = analyze_discards(hand, gold_tile, open_melds=open_melds)
        counts = Counter(hand)

        def key(analysis: DiscardAnalysis):
            next_hand = after_hand_without(hand, analysis.tile)
            effective_metric = self._effective_metric(analysis, next_hand, context)
            risk = self._risk_score(analysis.tile, hand, context)
            value = (
                self._hand_value(next_hand, gold_tile, open_melds)
                if self.abilities.hand_value
                else 0
            )
            gold_penalty = (
                self._gold_discard_penalty(analysis.tile, hand, gold_tile)
                if self.abilities.gold_strategy
                else int(analysis.tile == gold_tile)
            )
            youjin_bonus = self._youjin_value(next_hand, gold_tile) if self.abilities.youjin_strategy else 0
            kong_bonus = self._kong_value(next_hand, gold_tile) if self.abilities.kong_ev else 0
            monte_carlo = (
                self._monte_carlo_score(analysis, next_hand, context)
                if self.abilities.monte_carlo
                else 0.0
            )
            keep_score = self._keep_score(analysis.tile, counts)
            style_value_weight = self.style.value_weight if self.abilities.style_control else 1.0
            style_defense_weight = self.style.defense_weight if self.abilities.style_control else 1.0
            style_gold_weight = self.style.gold_weight if self.abilities.style_control else 1.0
            return (
                analysis.shanten,
                gold_penalty * style_gold_weight,
                -effective_metric,
                risk * style_defense_weight,
                -(value + youjin_bonus + kong_bonus) * style_value_weight,
                -monte_carlo,
                keep_score,
                TILE_INDEX[analysis.tile],
            )

        return min(analyses, key=key).tile

    def wants_pong(
        self,
        hand: List[str],
        tile: str,
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> bool:
        if not self.abilities.shanten:
            return super().wants_pong(hand, tile, gold_tile, open_melds, context)
        if not self.abilities.pong_ev:
            return self._wants_pong_by_shanten(hand, tile, gold_tile, open_melds)
        return self._wants_pong_by_ev(hand, tile, gold_tile, open_melds, context)

    def _effective_metric(
        self,
        analysis: DiscardAnalysis,
        next_hand: List[str],
        context: Optional[BotContext],
    ) -> int:
        if self.abilities.remaining_tiles and context:
            return context.remaining_effective_count(analysis.effective_draws, next_hand)
        if self.abilities.effective_draws:
            return analysis.effective_draw_count
        return 0

    def _remaining_effective_count(
        self,
        analysis: DiscardAnalysis,
        next_hand: List[str],
        gold_tile: str,
        open_melds: int,
        context: Optional[BotContext],
    ) -> int:
        if context:
            return context.remaining_effective_count(analysis.effective_draws, next_hand)
        return analysis.effective_draw_count

    def _wants_pong_by_shanten(
        self, hand: List[str], tile: str, gold_tile: str, open_melds: int
    ) -> bool:
        if tile == gold_tile or hand.count(tile) < 2:
            return False
        before = estimate_shanten(hand, gold_tile, open_melds=open_melds)
        after_hand = hand[:]
        after_hand.remove(tile)
        after_hand.remove(tile)
        best_after_discard = min(
            estimate_shanten(after_hand_without(after_hand, discard), gold_tile, open_melds + 1)
            for discard in set(after_hand)
        )
        basic_wants = super().wants_pong(hand, tile, gold_tile, open_melds=open_melds)
        return best_after_discard <= before and basic_wants

    def _wants_pong_by_ev(
        self,
        hand: List[str],
        tile: str,
        gold_tile: str,
        open_melds: int,
        context: Optional[BotContext],
    ) -> bool:
        if tile == gold_tile or hand.count(tile) < 2:
            return False

        before_shanten = estimate_shanten(hand, gold_tile, open_melds=open_melds)
        before_draws = effective_draws(hand, gold_tile, open_melds=open_melds)
        before_remaining = (
            context.remaining_effective_count(before_draws, hand)
            if self.abilities.remaining_tiles and context
            else len(before_draws)
        )

        after_hand = hand[:]
        after_hand.remove(tile)
        after_hand.remove(tile)
        best_after = None
        for discard in set(after_hand):
            candidate = after_hand_without(after_hand, discard)
            shanten = estimate_shanten(candidate, gold_tile, open_melds + 1)
            draws = effective_draws(candidate, gold_tile, open_melds + 1)
            remaining = (
                context.remaining_effective_count(draws, candidate)
                if self.abilities.remaining_tiles and context
                else len(draws)
            )
            value = (
                self._hand_value(candidate, gold_tile, open_melds + 1)
                if self.abilities.hand_value
                else 0
            )
            if self.abilities.kong_ev:
                value += self._kong_value(candidate, gold_tile)
            if self.abilities.youjin_strategy:
                value += self._youjin_value(candidate, gold_tile)
            score = (shanten, -remaining, -value)
            if best_after is None or score < best_after:
                best_after = score

        if best_after is None:
            return False

        before_value = (
            self._hand_value(hand, gold_tile, open_melds) if self.abilities.hand_value else 0
        )
        if self.abilities.kong_ev:
            before_value += self._kong_value(hand, gold_tile)
        if self.abilities.youjin_strategy:
            before_value += self._youjin_value(hand, gold_tile)
        before_score = (before_shanten, -before_remaining, -before_value)
        return best_after <= before_score

    def _hand_value(self, hand: List[str], gold_tile: str, open_melds: int) -> int:
        counts = Counter(hand)
        value = 0
        gold_count = counts[gold_tile]
        value += gold_count * 6
        if gold_count == 2:
            value += 8
        if gold_count >= 3:
            value += 30
        if open_melds == 0:
            pair_count = sum(1 for count in counts.values() if count >= 2)
            value += pair_count * 2
            if pair_count >= 5:
                value += 8
            orphan_kinds = len(set(hand) & TERMINALS_AND_HONORS)
            if orphan_kinds >= 10:
                value += 10
        return value

    def _gold_discard_penalty(self, tile: str, hand: List[str], gold_tile: str) -> int:
        if tile != gold_tile:
            return 0
        gold_count = hand.count(gold_tile)
        if gold_count >= 3:
            return 100
        if gold_count == 2:
            return 30
        return 8

    def _discard_risk(
        self, tile: str, own_hand: Sequence[str], context: Optional[BotContext]
    ) -> float:
        if context is None:
            return 0.0
        risk = 0.0
        visible_left = context.remaining_count(tile, own_hand)
        for player_index, discards in enumerate(context.discards_by_player):
            pressure = context.opponent_pressure(player_index)
            if pressure <= 0:
                continue
            if tile in discards:
                risk -= 0.4 * pressure
            else:
                risk += 0.6 * pressure
            if visible_left >= 3:
                risk += 0.4 * pressure
            if tile in HONORS and context.visible_counts.get(tile, 0) == 0:
                risk += 0.2 * pressure
        return max(0.0, risk)

    def _risk_score(
        self, tile: str, own_hand: Sequence[str], context: Optional[BotContext]
    ) -> float:
        if not self.abilities.defense:
            return 0.0
        if self.abilities.danger_refined:
            return self._refined_danger(tile, own_hand, context)
        return self._discard_risk(tile, own_hand, context)

    def _refined_danger(
        self, tile: str, own_hand: Sequence[str], context: Optional[BotContext]
    ) -> float:
        if context is None:
            return 0.0
        danger = self._discard_risk(tile, own_hand, context)
        live_count = context.remaining_count(tile, own_hand)
        for player_index, discards in enumerate(context.discards_by_player):
            likelihood = (
                context.opponent_tenpai_likelihood(player_index)
                if self.abilities.opponent_tenpai
                else context.opponent_pressure(player_index) * 0.25
            )
            if likelihood <= 0:
                continue
            if tile in discards:
                danger -= 0.6 * likelihood
            else:
                danger += 0.5 * likelihood
            if tile in HONORS and context.visible_counts.get(tile, 0) == 0:
                danger += 0.5 * likelihood
            if is_numbered(tile):
                number = tile_number(tile)
                if 3 <= number <= 7 and live_count >= 2:
                    danger += 0.35 * likelihood
                if number in (1, 9) and context.visible_counts.get(tile, 0) >= 2:
                    danger -= 0.25 * likelihood
        return max(0.0, danger)

    def _kong_value(self, hand: Sequence[str], gold_tile: str) -> int:
        counts = Counter(tile for tile in hand if tile != gold_tile)
        value = 0
        for count in counts.values():
            if count >= 4:
                value += 10
            elif count == 3:
                value += 3
        return value

    def _youjin_value(self, hand: Sequence[str], gold_tile: str) -> int:
        gold_count = hand.count(gold_tile)
        if gold_count == 0:
            return 0
        counts = Counter(tile for tile in hand if tile != gold_tile)
        pair_like = sum(1 for count in counts.values() if count >= 2)
        value = gold_count * 3
        if gold_count >= 2:
            value += 8
        if pair_like >= 1:
            value += 3
        return value

    def _monte_carlo_score(
        self,
        analysis: DiscardAnalysis,
        next_hand: Sequence[str],
        context: Optional[BotContext],
    ) -> float:
        if context is None or context.wall_remaining <= 0:
            return float(analysis.effective_draw_count)
        remaining = context.remaining_effective_count(analysis.effective_draws, next_hand)
        draw_rate = remaining / max(1, context.wall_remaining)
        return draw_rate * 100.0

    def explain_discard(
        self,
        hand: List[str],
        gold_tile: str,
        open_melds: int = 0,
        context: Optional[BotContext] = None,
    ) -> str:
        tile = self.choose_discard(hand, gold_tile, open_melds, context)
        if not self.abilities.explanation:
            return f"建议打出 {tile}。"
        next_hand = after_hand_without(hand, tile)
        shanten = estimate_shanten(next_hand, gold_tile, open_melds) if self.abilities.shanten else None
        draws = effective_draws(next_hand, gold_tile, open_melds) if self.abilities.effective_draws else []
        remaining = (
            context.remaining_effective_count(draws, next_hand)
            if self.abilities.remaining_tiles and context
            else len(draws)
        )
        parts = [f"建议打出 {tile}"]
        if shanten is not None:
            parts.append(f"向听 {shanten}")
        if self.abilities.effective_draws:
            parts.append(f"有效进张 {len(draws)} 种")
        if self.abilities.remaining_tiles:
            parts.append(f"剩余有效张 {remaining}")
        if self.abilities.defense and context:
            parts.append(f"风险 {self._risk_score(tile, hand, context):.2f}")
        return "，".join(parts) + "。"


@dataclass
class ExpertBot(ConfigurableBot):
    """Compatibility wrapper for the full current expert ability set."""

    name: str = "专家机器人"
    abilities: AbilityConfig = field(default_factory=AbilityConfig.expert)


def after_hand_without(hand: List[str], tile: str) -> List[str]:
    next_hand = hand[:]
    next_hand.remove(tile)
    return next_hand


def build_bot_from_abilities(name: str, abilities: AbilityConfig) -> BotPolicy:
    if abilities == AbilityConfig.basic():
        return BasicBot(name=name)
    if abilities.shanten and not any(
        [
            abilities.effective_draws,
            abilities.remaining_tiles,
            abilities.hand_value,
            abilities.pong_ev,
            abilities.defense,
            abilities.gold_strategy,
            abilities.style_control,
            abilities.opponent_tenpai,
            abilities.danger_refined,
            abilities.kong_ev,
            abilities.youjin_strategy,
            abilities.monte_carlo,
            abilities.explanation,
        ]
    ):
        return ShantenBot(name=name, use_effective_draws=False)
    return ConfigurableBot(name=name, abilities=abilities)


def default_bot_policies() -> List[BotPolicy]:
    return [
        build_bot_from_abilities("机器人A-基础", AbilityConfig.basic()),
        build_bot_from_abilities("机器人B-会算向听", AbilityConfig.shanten_only()),
        build_bot_from_abilities("机器人C-专家:牌河/价值/防守/金牌", AbilityConfig.expert()),
    ]
