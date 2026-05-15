"""Tile definitions and display helpers."""

from typing import Dict, Iterable, List


SUITS = ("M", "T", "S")
HONORS = ("EAST", "SOUTH", "WEST", "NORTH", "RED", "GREEN", "WHITE")
FLOWERS = ("SPRING", "SUMMER", "AUTUMN", "WINTER", "PLUM", "ORCHID", "BAMBOO", "CHRYSANTHEMUM")

PLAYABLE_TILES: List[str] = (
    [f"M{i}" for i in range(1, 10)]
    + [f"T{i}" for i in range(1, 10)]
    + [f"S{i}" for i in range(1, 10)]
    + list(HONORS)
)
TILE_ORDER: List[str] = PLAYABLE_TILES + list(FLOWERS)

TILE_INDEX: Dict[str, int] = {tile: index for index, tile in enumerate(TILE_ORDER)}

DISPLAY: Dict[str, str] = {}
for i in range(1, 10):
    DISPLAY[f"M{i}"] = f"{i}万"
    DISPLAY[f"T{i}"] = f"{i}筒"
    DISPLAY[f"S{i}"] = f"{i}条"
DISPLAY.update(
    {
        "EAST": "东",
        "SOUTH": "南",
        "WEST": "西",
        "NORTH": "北",
        "RED": "中",
        "GREEN": "发",
        "WHITE": "白",
        "SPRING": "春",
        "SUMMER": "夏",
        "AUTUMN": "秋",
        "WINTER": "冬",
        "PLUM": "梅",
        "ORCHID": "兰",
        "BAMBOO": "竹",
        "CHRYSANTHEMUM": "菊",
    }
)

TERMINALS_AND_HONORS = set(HONORS)
for suit in SUITS:
    TERMINALS_AND_HONORS.add(f"{suit}1")
    TERMINALS_AND_HONORS.add(f"{suit}9")


def build_wall(include_flowers: bool = False) -> List[str]:
    """Return a fresh wall, optionally with the 8 flower tiles."""
    wall: List[str] = []
    for tile in PLAYABLE_TILES:
        wall.extend([tile] * 4)
    if include_flowers:
        wall.extend(FLOWERS)
    return wall


def is_flower(tile: str) -> bool:
    return tile in FLOWERS


def is_numbered(tile: str) -> bool:
    return len(tile) == 2 and tile[:1] in SUITS and tile[1:].isdigit()


def tile_number(tile: str) -> int:
    if not is_numbered(tile):
        raise ValueError(f"Honor tile has no number: {tile}")
    return int(tile[1:])


def sort_tiles(tiles: Iterable[str]) -> List[str]:
    return sorted(tiles, key=lambda tile: TILE_INDEX[tile])


def display_tile(tile: str) -> str:
    return DISPLAY[tile]


def display_tiles(tiles: Iterable[str]) -> str:
    return " ".join(display_tile(tile) for tile in sort_tiles(tiles))
