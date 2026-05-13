"""Bot policies with different playing strengths."""

from collections import Counter
from dataclasses import dataclass
from typing import List, Protocol

from .shanten import analyze_discards, estimate_shanten
from .tiles import HONORS, TILE_INDEX, is_numbered, tile_number


class BotPolicy(Protocol):
    name: str

    def choose_discard(self, hand: List[str], gold_tile: str, open_melds: int = 0) -> str:
        ...

    def wants_pong(
        self, hand: List[str], tile: str, gold_tile: str, open_melds: int = 0
    ) -> bool:
        ...


@dataclass
class BasicBot:
    """A conservative bot that keeps pairs, neighbors and gold tiles."""

    name: str = "基础机器人"

    def choose_discard(self, hand: List[str], gold_tile: str, open_melds: int = 0) -> str:
        candidates = [tile for tile in hand if tile != gold_tile]
        if not candidates:
            return hand[0]
        counts = Counter(hand)
        return min(candidates, key=lambda tile: (self._keep_score(tile, counts), TILE_INDEX[tile]))

    def wants_pong(
        self, hand: List[str], tile: str, gold_tile: str, open_melds: int = 0
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

    def choose_discard(self, hand: List[str], gold_tile: str, open_melds: int = 0) -> str:
        analyses = analyze_discards(hand, gold_tile, open_melds=open_melds)
        counts = Counter(hand)

        def key(analysis):
            effective_part = -analysis.effective_draw_count if self.use_effective_draws else 0
            gold_penalty = 1 if analysis.tile == gold_tile else 0
            keep_score = self._keep_score(analysis.tile, counts)
            return (
                analysis.shanten,
                gold_penalty,
                effective_part,
                keep_score,
                TILE_INDEX[analysis.tile],
            )

        return min(analyses, key=key).tile

    def wants_pong(
        self, hand: List[str], tile: str, gold_tile: str, open_melds: int = 0
    ) -> bool:
        if tile == gold_tile or hand.count(tile) < 2:
            return False
        if not self.allow_shanten_pong:
            return super().wants_pong(hand, tile, gold_tile, open_melds=open_melds)

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


def after_hand_without(hand: List[str], tile: str) -> List[str]:
    next_hand = hand[:]
    next_hand.remove(tile)
    return next_hand


def default_bot_policies() -> List[BotPolicy]:
    return [
        BasicBot(name="机器人A-基础"),
        ShantenBot(name="机器人B-会算向听", use_effective_draws=False),
        ShantenBot(name="机器人C-会算向听和进张", use_effective_draws=True),
    ]
