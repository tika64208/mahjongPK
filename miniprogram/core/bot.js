const { HONORS, TILE_INDEX, isNumbered, tileNumber } = require("./tiles");

function chooseDiscard(hand, goldTile) {
  const candidates = hand.filter((tile) => tile !== goldTile);
  if (!candidates.length) {
    return hand[0];
  }
  const counts = countTiles(hand);
  return candidates.slice().sort((left, right) => {
    const leftScore = keepScore(left, counts);
    const rightScore = keepScore(right, counts);
    if (leftScore !== rightScore) {
      return leftScore - rightScore;
    }
    return TILE_INDEX[left] - TILE_INDEX[right];
  })[0];
}

function wantsPong(hand, tile, goldTile) {
  if (tile === goldTile || countTile(hand, tile) < 2) {
    return false;
  }
  if (HONORS.indexOf(tile) >= 0) {
    return true;
  }
  return neighborCount(hand, tile) === 0;
}

function wantsExposedKong(hand, tile, goldTile) {
  return tile !== goldTile && countTile(hand, tile) >= 3;
}

function wantsSelfKong(hand, tile, goldTile) {
  return tile !== goldTile && countTile(hand, tile) >= 4;
}

function keepScore(tile, counts) {
  let score = 0;
  if ((counts[tile] || 0) >= 2) {
    score += 4;
  }
  if ((counts[tile] || 0) >= 3) {
    score += 3;
  }
  if (HONORS.indexOf(tile) >= 0) {
    return score;
  }
  score += neighborCount(Object.keys(counts).flatMap((item) => Array(counts[item]).fill(item)), tile);
  return score;
}

function neighborCount(hand, tile) {
  if (!isNumbered(tile)) {
    return 0;
  }
  const suit = tile.slice(0, 1);
  const number = tileNumber(tile);
  return [-2, -1, 1, 2].filter((offset) => {
    const next = number + offset;
    return next >= 1 && next <= 9 && hand.indexOf(`${suit}${next}`) >= 0;
  }).length;
}

function countTiles(tiles) {
  return tiles.reduce((counts, tile) => {
    counts[tile] = (counts[tile] || 0) + 1;
    return counts;
  }, {});
}

function countTile(tiles, tile) {
  return tiles.filter((item) => item === tile).length;
}

module.exports = {
  chooseDiscard,
  wantsPong,
  wantsExposedKong,
  wantsSelfKong,
  countTile,
};
