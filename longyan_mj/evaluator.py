"""Winning-hand evaluation for the first Longyan Mahjong MVP."""

from collections import Counter
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

from .tiles import TERMINALS_AND_HONORS, TILE_INDEX, TILE_ORDER, is_numbered, tile_number


class WinResult:
    """A small value object for a winning hand."""

    def __init__(self, kind: str, label: str, multiplier: int) -> None:
        self.kind = kind
        self.label = label
        self.multiplier = multiplier

    def __repr__(self) -> str:
        return f"WinResult(kind={self.kind!r}, multiplier={self.multiplier!r})"


def count_gold(tiles: Iterable[str], gold_tile: str) -> int:
    return sum(1 for tile in tiles if tile == gold_tile)


def evaluate_win(
    tiles: Iterable[str], gold_tile: Optional[str], open_melds: int = 0
) -> Optional[WinResult]:
    """Return the best supported win result, or None.

    The MVP supports three-gold, seven-pairs, thirteen-orphans and standard
    4-sets-plus-pair hands. Gold tiles are wildcards for hand evaluation.
    """
    hand = list(tiles)
    if gold_tile and count_gold(hand, gold_tile) >= 3:
        return WinResult("three_gold", "三金倒", 3)
    if open_melds == 0 and gold_tile and is_thirteen_orphans(hand, gold_tile):
        return WinResult("thirteen_orphans", "十三幺", 20)
    if open_melds == 0 and gold_tile and is_seven_pairs(hand, gold_tile):
        return WinResult("seven_pairs", "七对", 3)
    if is_standard_win(hand, gold_tile, open_melds=open_melds):
        return WinResult("standard", "自摸", 1)
    return None


def find_youjin_discard(
    tiles: Iterable[str], gold_tile: Optional[str], open_melds: int = 0
) -> Optional[str]:
    """Return a natural pair tile that can be discarded to enter youjin.

    MVP rule: if the hand is a standard winning hand and one gold can serve as
    the pair with a natural tile, discarding that natural tile leaves the gold as
    single pair anchor for single-you.
    """
    if not gold_tile:
        return None
    hand = list(tiles)
    if hand.count(gold_tile) != 1:
        return None
    if not is_standard_win(hand, gold_tile, open_melds=open_melds):
        return None

    counts = Counter(tile for tile in hand if tile != gold_tile)
    for tile in sorted(counts, key=lambda item: TILE_INDEX[item]):
        if counts[tile] >= 1:
            candidate = hand[:]
            candidate.remove(tile)
            if is_standard_win(candidate + [tile], gold_tile, open_melds=open_melds):
                without_gold = [item for item in candidate if item != gold_tile]
                if _can_form_melds(_counts_tuple(Counter(without_gold)), 0, 4 - open_melds):
                    return tile
    return None


def is_seven_pairs(tiles: Iterable[str], gold_tile: str) -> bool:
    hand = list(tiles)
    if len(hand) != 14:
        return False
    wildcards = count_gold(hand, gold_tile)
    counts = Counter(tile for tile in hand if tile != gold_tile)
    odd_count = sum(1 for count in counts.values() if count % 2 == 1)
    return wildcards >= odd_count and (wildcards - odd_count) % 2 == 0


def is_thirteen_orphans(tiles: Iterable[str], gold_tile: str) -> bool:
    hand = list(tiles)
    if len(hand) != 14:
        return False
    wildcards = count_gold(hand, gold_tile)
    counts = Counter(tile for tile in hand if tile != gold_tile)
    if any(tile not in TERMINALS_AND_HONORS for tile in counts):
        return False

    missing = sum(1 for tile in TERMINALS_AND_HONORS if counts.get(tile, 0) == 0)
    if missing > wildcards:
        return False

    remaining_wildcards = wildcards - missing
    has_natural_pair = any(counts.get(tile, 0) >= 2 for tile in TERMINALS_AND_HONORS)
    return has_natural_pair or remaining_wildcards >= 1


def is_standard_win(
    tiles: Iterable[str], gold_tile: Optional[str], open_melds: int = 0
) -> bool:
    hand = list(tiles)
    sets_needed = 4 - open_melds
    if sets_needed < 0:
        return False
    if len(hand) != sets_needed * 3 + 2:
        return False

    wildcards = count_gold(hand, gold_tile) if gold_tile else 0
    counts = Counter(tile for tile in hand if tile != gold_tile)
    counts_tuple = _counts_tuple(counts)

    for index, count in enumerate(counts_tuple):
        if count <= 0:
            continue
        take = min(2, count)
        need = 2 - take
        if need <= wildcards:
            next_counts = list(counts_tuple)
            next_counts[index] -= take
            if _can_form_melds(tuple(next_counts), wildcards - need, sets_needed):
                return True

    if wildcards >= 2 and _can_form_melds(counts_tuple, wildcards - 2, sets_needed):
        return True

    return False


def _counts_tuple(counts: Dict[str, int]) -> tuple:
    return tuple(counts.get(tile, 0) for tile in TILE_ORDER)


@lru_cache(maxsize=None)
def _can_form_melds(counts_tuple: tuple, wildcards: int, sets_needed: int) -> bool:
    if sets_needed == 0:
        return sum(counts_tuple) == 0

    first = _first_non_zero(counts_tuple)
    if first is None:
        return wildcards >= sets_needed * 3

    counts = list(counts_tuple)

    triplet_take = min(3, counts[first])
    triplet_need = 3 - triplet_take
    if triplet_need <= wildcards:
        next_counts = counts[:]
        next_counts[first] -= triplet_take
        if _can_form_melds(tuple(next_counts), wildcards - triplet_need, sets_needed - 1):
            return True

    if _can_make_sequence_from(first):
        indexes = [first, first + 1, first + 2]
        sequence_need = sum(1 for index in indexes if counts[index] == 0)
        if sequence_need <= wildcards:
            next_counts = counts[:]
            for index in indexes:
                if next_counts[index] > 0:
                    next_counts[index] -= 1
            if _can_form_melds(tuple(next_counts), wildcards - sequence_need, sets_needed - 1):
                return True

    return False


def _first_non_zero(counts_tuple: tuple) -> Optional[int]:
    for index, count in enumerate(counts_tuple):
        if count > 0:
            return index
    return None


def _can_make_sequence_from(index: int) -> bool:
    tile = TILE_ORDER[index]
    if not is_numbered(tile):
        return False
    return tile_number(tile) <= 7 and TILE_ORDER[index + 1][:1] == tile[:1]
