const SUITS = ["M", "T", "S"];
const HONORS = ["EAST", "SOUTH", "WEST", "NORTH", "RED", "GREEN", "WHITE"];
const FLOWERS = ["SPRING", "SUMMER", "AUTUMN", "WINTER", "PLUM", "ORCHID", "BAMBOO", "CHRYSANTHEMUM"];

const PLAYABLE_TILES = []
  .concat(...SUITS.map((suit) => Array.from({ length: 9 }, (_, index) => `${suit}${index + 1}`)))
  .concat(HONORS);
const TILE_ORDER = PLAYABLE_TILES.concat(FLOWERS);
const TILE_INDEX = TILE_ORDER.reduce((indexes, tile, index) => {
  indexes[tile] = index;
  return indexes;
}, {});

const DISPLAY = {
  EAST: "东",
  SOUTH: "南",
  WEST: "西",
  NORTH: "北",
  RED: "中",
  GREEN: "发",
  WHITE: "白",
  SPRING: "春",
  SUMMER: "夏",
  AUTUMN: "秋",
  WINTER: "冬",
  PLUM: "梅",
  ORCHID: "兰",
  BAMBOO: "竹",
  CHRYSANTHEMUM: "菊",
};

SUITS.forEach((suit) => {
  for (let number = 1; number <= 9; number += 1) {
    const suffix = suit === "M" ? "万" : suit === "T" ? "筒" : "条";
    DISPLAY[`${suit}${number}`] = `${number}${suffix}`;
  }
});

const TERMINALS_AND_HONORS = new Set(HONORS);
SUITS.forEach((suit) => {
  TERMINALS_AND_HONORS.add(`${suit}1`);
  TERMINALS_AND_HONORS.add(`${suit}9`);
});

function buildWall(includeFlowers = true) {
  const wall = [];
  PLAYABLE_TILES.forEach((tile) => {
    for (let index = 0; index < 4; index += 1) {
      wall.push(tile);
    }
  });
  if (includeFlowers) {
    wall.push(...FLOWERS);
  }
  return wall;
}

function isFlower(tile) {
  return FLOWERS.indexOf(tile) >= 0;
}

function isNumbered(tile) {
  return /^[MTS][1-9]$/.test(tile);
}

function tileNumber(tile) {
  return Number(tile.slice(1));
}

function sortTiles(tiles) {
  return tiles.slice().sort((left, right) => TILE_INDEX[left] - TILE_INDEX[right]);
}

function displayTile(tile) {
  return DISPLAY[tile] || tile;
}

function displayTiles(tiles) {
  return sortTiles(tiles).map(displayTile).join(" ");
}

module.exports = {
  SUITS,
  HONORS,
  FLOWERS,
  PLAYABLE_TILES,
  TILE_ORDER,
  TILE_INDEX,
  TERMINALS_AND_HONORS,
  buildWall,
  isFlower,
  isNumbered,
  tileNumber,
  sortTiles,
  displayTile,
  displayTiles,
};
