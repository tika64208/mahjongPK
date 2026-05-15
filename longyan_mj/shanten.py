"""Shanten and effective-draw helpers for bot decisions."""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Optional, Set, Tuple

from .evaluator import evaluate_win
from .tiles import PLAYABLE_TILES, TILE_INDEX, is_numbered


@dataclass(frozen=True)
class DiscardAnalysis:
    tile: str
    shanten: int
    effective_draws: Tuple[str, ...]

    @property
    def effective_draw_count(self) -> int:
        return len(self.effective_draws)


def analyze_discards(
    hand: Iterable[str], gold_tile: str, open_melds: int = 0
) -> List[DiscardAnalysis]:
    """Analyze every distinct discard from a complete hand."""
    hand_list = list(hand)
    analyses: List[DiscardAnalysis] = []
    for tile in sorted(set(hand_list), key=lambda item: TILE_INDEX[item]):
        next_hand = hand_list[:]
        next_hand.remove(tile)
        draws = tuple(effective_draws(next_hand, gold_tile, open_melds=open_melds))
        analyses.append(
            DiscardAnalysis(
                tile=tile,
                shanten=estimate_shanten(next_hand, gold_tile, open_melds=open_melds),
                effective_draws=draws,
            )
        )
    return analyses


def effective_draws(
    tiles: Iterable[str], gold_tile: str, open_melds: int = 0
) -> List[str]:
    """Return tile kinds that complete the hand if drawn next."""
    return list(
        _effective_draws_cached(_hand_key(tiles), gold_tile, open_melds)
    )


@lru_cache(maxsize=200000)
def _effective_draws_cached(
    hand_key: Tuple[str, ...], gold_tile: str, open_melds: int
) -> Tuple[str, ...]:
    hand = list(hand_key)
    draws: List[str] = []
    for tile in PLAYABLE_TILES:
        candidate = hand + [tile]
        if evaluate_win(candidate, gold_tile, open_melds=open_melds):
            draws.append(tile)
    return tuple(draws)


def estimate_shanten(tiles: Iterable[str], gold_tile: str, open_melds: int = 0) -> int:
    """Estimate shanten for a concealed hand fragment.

    The estimate is exact for already-winning and tenpai checks because it uses
    the real evaluator for the next draw. For farther-away hands it combines
    standard-hand, seven-pairs and thirteen-orphans shape estimates.
    """
    return _estimate_shanten_cached(_hand_key(tiles), gold_tile, open_melds)


@lru_cache(maxsize=200000)
def _estimate_shanten_cached(
    hand_key: Tuple[str, ...], gold_tile: str, open_melds: int
) -> int:
    hand = list(hand_key)
    sets_needed = 4 - open_melds
    if sets_needed < 0:
        return 8

    if len(hand) == sets_needed * 3 + 2:
        if evaluate_win(hand, gold_tile, open_melds=open_melds):
            return -1
        return min(
            _standard_shanten(hand, gold_tile, open_melds),
            _seven_pairs_shanten(hand, gold_tile, open_melds),
            _thirteen_orphans_shanten(hand, gold_tile, open_melds),
        )

    if len(hand) == sets_needed * 3 + 1 and effective_draws(hand, gold_tile, open_melds):
        return 0

    return min(
        _standard_shanten(hand, gold_tile, open_melds),
        _seven_pairs_shanten(hand, gold_tile, open_melds),
        _thirteen_orphans_shanten(hand, gold_tile, open_melds),
    )


def _hand_key(tiles: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(tiles, key=lambda tile: TILE_INDEX[tile]))


def _standard_shanten(tiles: List[str], gold_tile: str, open_melds: int) -> int:
    wildcards = tiles.count(gold_tile)
    counts = Counter(tile for tile in tiles if tile != gold_tile)
    shapes = _shape_options(_counts_tuple(counts))
    best = 8
    for melds, taatsu, pair in shapes:
        total_melds = min(4, melds + open_melds)
        usable_taatsu = min(taatsu, 4 - total_melds)
        shanten = 8 - total_melds * 2 - usable_taatsu - min(pair, 1)
        best = min(best, shanten)
    return max(-1, best - wildcards)


def _seven_pairs_shanten(tiles: List[str], gold_tile: str, open_melds: int) -> int:
    if open_melds:
        return 8
    wildcards = tiles.count(gold_tile)
    counts = Counter(tile for tile in tiles if tile != gold_tile)
    pairs = sum(1 for count in counts.values() if count >= 2)
    singles = sum(1 for count in counts.values() if count == 1)
    wildcard_pairs = min(wildcards, singles)
    pairs += wildcard_pairs
    remaining_wildcards = wildcards - wildcard_pairs
    pairs += remaining_wildcards // 2
    unique_kinds = len(counts) + remaining_wildcards
    return max(0, 6 - pairs + max(0, 7 - unique_kinds))


def _thirteen_orphans_shanten(tiles: List[str], gold_tile: str, open_melds: int) -> int:
    if open_melds:
        return 8
    from .tiles import TERMINALS_AND_HONORS

    wildcards = tiles.count(gold_tile)
    counts = Counter(tile for tile in tiles if tile != gold_tile)
    unique = sum(1 for tile in TERMINALS_AND_HONORS if counts.get(tile, 0) > 0)
    has_pair = any(counts.get(tile, 0) >= 2 for tile in TERMINALS_AND_HONORS)
    missing = 13 - unique
    need_pair = 0 if has_pair else 1
    return max(0, missing + need_pair - wildcards)


def _counts_tuple(counts: Counter) -> Tuple[int, ...]:
    return tuple(counts.get(tile, 0) for tile in PLAYABLE_TILES)


@lru_cache(maxsize=None)
def _shape_options(counts_tuple: Tuple[int, ...]) -> frozenset:
    first = _first_non_zero(counts_tuple)
    if first is None:
        return frozenset({(0, 0, 0)})

    counts = list(counts_tuple)
    results: Set[Tuple[int, int, int]] = set()

    def add_options(next_counts: List[int], add_meld: int, add_taatsu: int, add_pair: int) -> None:
        for melds, taatsu, pair in _shape_options(tuple(next_counts)):
            results.add((melds + add_meld, taatsu + add_taatsu, min(1, pair + add_pair)))

    skipped = counts[:]
    skipped[first] -= 1
    add_options(skipped, 0, 0, 0)

    if counts[first] >= 3:
        next_counts = counts[:]
        next_counts[first] -= 3
        add_options(next_counts, 1, 0, 0)

    if _can_start_sequence(first) and counts[first + 1] > 0 and counts[first + 2] > 0:
        next_counts = counts[:]
        next_counts[first] -= 1
        next_counts[first + 1] -= 1
        next_counts[first + 2] -= 1
        add_options(next_counts, 1, 0, 0)

    if counts[first] >= 2:
        next_counts = counts[:]
        next_counts[first] -= 2
        add_options(next_counts, 0, 1, 1)

    if _can_start_sequence(first) and counts[first + 1] > 0:
        next_counts = counts[:]
        next_counts[first] -= 1
        next_counts[first + 1] -= 1
        add_options(next_counts, 0, 1, 0)

    if _can_start_sequence(first) and counts[first + 2] > 0:
        next_counts = counts[:]
        next_counts[first] -= 1
        next_counts[first + 2] -= 1
        add_options(next_counts, 0, 1, 0)

    return frozenset(results)


def _first_non_zero(counts_tuple: Tuple[int, ...]) -> Optional[int]:
    for index, count in enumerate(counts_tuple):
        if count > 0:
            return index
    return None


def _can_start_sequence(index: int) -> bool:
    tile = PLAYABLE_TILES[index]
    if not is_numbered(tile):
        return False
    return index + 2 < len(PLAYABLE_TILES) and PLAYABLE_TILES[index + 2][:1] == tile[:1]
