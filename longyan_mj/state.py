"""Game state models."""

from dataclasses import dataclass, field
from typing import List

from .tiles import sort_tiles


@dataclass
class Meld:
    kind: str
    tiles: List[str]
    source_player: int


@dataclass
class Player:
    name: str
    is_human: bool = False
    hand: List[str] = field(default_factory=list)
    melds: List[Meld] = field(default_factory=list)
    flowers: List[str] = field(default_factory=list)
    youjin_level: int = 0

    def sort_hand(self) -> None:
        self.hand = sort_tiles(self.hand)

    def can_pong(self, tile: str, gold_tile: str) -> bool:
        return tile != gold_tile and self.hand.count(tile) >= 2

    def can_exposed_kong(self, tile: str, gold_tile: str) -> bool:
        return tile != gold_tile and self.hand.count(tile) >= 3

    def can_concealed_kong(self, tile: str, gold_tile: str) -> bool:
        return tile != gold_tile and self.hand.count(tile) >= 4

    def can_added_kong(self, tile: str, gold_tile: str) -> bool:
        if tile == gold_tile or tile not in self.hand:
            return False
        return any(meld.kind == "pong" and meld.tiles[0] == tile for meld in self.melds)

    def pong(self, tile: str, source_player: int) -> None:
        removed = 0
        next_hand: List[str] = []
        for hand_tile in self.hand:
            if hand_tile == tile and removed < 2:
                removed += 1
            else:
                next_hand.append(hand_tile)
        if removed != 2:
            raise ValueError(f"{self.name} cannot pong {tile}")
        self.hand = sort_tiles(next_hand)
        self.melds.append(Meld(kind="pong", tiles=[tile, tile, tile], source_player=source_player))

    def exposed_kong(self, tile: str, source_player: int) -> None:
        self._remove_copies(tile, 3)
        self.melds.append(
            Meld(kind="exposed_kong", tiles=[tile, tile, tile, tile], source_player=source_player)
        )

    def concealed_kong(self, tile: str, source_player: int) -> None:
        self._remove_copies(tile, 4)
        self.melds.append(
            Meld(kind="concealed_kong", tiles=[tile, tile, tile, tile], source_player=source_player)
        )

    def added_kong(self, tile: str) -> None:
        self.remove_tile(tile)
        for meld in self.melds:
            if meld.kind == "pong" and meld.tiles[0] == tile:
                meld.kind = "added_kong"
                meld.tiles = [tile, tile, tile, tile]
                return
        raise ValueError(f"{self.name} cannot add kong {tile}")

    def remove_tile_at(self, index: int) -> str:
        tile = self.hand.pop(index)
        self.sort_hand()
        return tile

    def remove_tile(self, tile: str) -> str:
        self.hand.remove(tile)
        self.sort_hand()
        return tile

    def clear_youjin(self) -> None:
        self.youjin_level = 0

    def _remove_copies(self, tile: str, copies: int) -> None:
        removed = 0
        next_hand: List[str] = []
        for hand_tile in self.hand:
            if hand_tile == tile and removed < copies:
                removed += 1
            else:
                next_hand.append(hand_tile)
        if removed != copies:
            raise ValueError(f"{self.name} cannot remove {copies} copies of {tile}")
        self.hand = sort_tiles(next_hand)
