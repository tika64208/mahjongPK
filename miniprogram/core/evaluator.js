const {
  PLAYABLE_TILES,
  TERMINALS_AND_HONORS,
  TILE_INDEX,
  isNumbered,
  tileNumber,
} = require("./tiles");

function countGold(tiles, goldTile) {
  if (!goldTile) {
    return 0;
  }
  return tiles.filter((tile) => tile === goldTile).length;
}

function evaluateWin(tiles, goldTile, openMelds = 0) {
  const hand = tiles.slice();
  if (goldTile && countGold(hand, goldTile) >= 3) {
    return { kind: "three_gold", label: "三金倒", multiplier: 3 };
  }
  if (openMelds === 0 && goldTile && isThirteenOrphans(hand, goldTile)) {
    return { kind: "thirteen_orphans", label: "十三幺", multiplier: 20 };
  }
  if (openMelds === 0 && goldTile && isSevenPairs(hand, goldTile)) {
    return { kind: "seven_pairs", label: "七对", multiplier: 3 };
  }
  if (isStandardWin(hand, goldTile, openMelds)) {
    return { kind: "standard", label: "自摸", multiplier: 1 };
  }
  return null;
}

function evaluateQiangjin(tiles, goldTile, openMelds = 0) {
  if (!goldTile) {
    return null;
  }
  const hand = tiles.slice();
  if (hand.length === openMelds * 3 + 13) {
    if (isQiangjinShape(hand.concat([goldTile]), goldTile, openMelds)) {
      return { kind: "qiang_jin", label: "抢金", multiplier: 4 };
    }
  }
  if (hand.length === openMelds * 3 + 14) {
    const uniqueTiles = Array.from(new Set(hand)).sort((a, b) => TILE_INDEX[a] - TILE_INDEX[b]);
    for (let index = 0; index < uniqueTiles.length; index += 1) {
      const candidate = hand.slice();
      candidate.splice(candidate.indexOf(uniqueTiles[index]), 1);
      if (isQiangjinShape(candidate.concat([goldTile]), goldTile, openMelds)) {
        return { kind: "qiang_jin", label: "抢金", multiplier: 4 };
      }
    }
  }
  return null;
}

function findYoujinDiscard(tiles, goldTile, openMelds = 0) {
  if (!goldTile) {
    return null;
  }
  const hand = tiles.slice();
  if (countGold(hand, goldTile) >= 3 || !isStandardWin(hand, goldTile, openMelds)) {
    return null;
  }
  const uniqueTiles = Array.from(new Set(hand.filter((tile) => tile !== goldTile)))
    .sort((a, b) => TILE_INDEX[a] - TILE_INDEX[b]);
  for (let index = 0; index < uniqueTiles.length; index += 1) {
    const tile = uniqueTiles[index];
    const candidate = hand.slice();
    candidate.splice(candidate.indexOf(tile), 1);
    if (isYoujinWait(candidate, goldTile, openMelds)) {
      return tile;
    }
  }
  return null;
}

function isQiangjinShape(tiles, goldTile, openMelds) {
  if (openMelds === 0 && isThirteenOrphans(tiles, goldTile)) {
    return true;
  }
  if (openMelds === 0 && isSevenPairs(tiles, goldTile)) {
    return true;
  }
  return isStandardWin(tiles, goldTile, openMelds);
}

function isYoujinWait(tiles, goldTile, openMelds) {
  const setsNeeded = 4 - openMelds;
  if (tiles.length !== setsNeeded * 3 + 1) {
    return false;
  }
  return PLAYABLE_TILES.every((draw) => evaluateWin(tiles.concat([draw]), goldTile, openMelds));
}

function isSevenPairs(tiles, goldTile) {
  if (tiles.length !== 14) {
    return false;
  }
  const wildcards = countGold(tiles, goldTile);
  const counts = countTiles(tiles.filter((tile) => tile !== goldTile));
  const oddCount = Object.keys(counts).filter((tile) => counts[tile] % 2 === 1).length;
  return wildcards >= oddCount && (wildcards - oddCount) % 2 === 0;
}

function isThirteenOrphans(tiles, goldTile) {
  if (tiles.length !== 14) {
    return false;
  }
  const wildcards = countGold(tiles, goldTile);
  const counts = countTiles(tiles.filter((tile) => tile !== goldTile));
  const countKeys = Object.keys(counts);
  if (countKeys.some((tile) => !TERMINALS_AND_HONORS.has(tile))) {
    return false;
  }
  const missing = Array.from(TERMINALS_AND_HONORS).filter((tile) => !counts[tile]).length;
  if (missing > wildcards) {
    return false;
  }
  const remainingWildcards = wildcards - missing;
  const hasNaturalPair = Array.from(TERMINALS_AND_HONORS).some((tile) => counts[tile] >= 2);
  return hasNaturalPair || remainingWildcards >= 1;
}

function isStandardWin(tiles, goldTile, openMelds = 0) {
  const hand = tiles.slice();
  const setsNeeded = 4 - openMelds;
  if (setsNeeded < 0 || hand.length !== setsNeeded * 3 + 2) {
    return false;
  }
  const wildcards = countGold(hand, goldTile);
  const counts = countTiles(hand.filter((tile) => tile !== goldTile));
  const tuple = countsTuple(counts);

  for (let index = 0; index < tuple.length; index += 1) {
    const count = tuple[index];
    if (count <= 0) {
      continue;
    }
    const pairTakes = [];
    if (count >= 2) {
      pairTakes.push(2);
    }
    if (count >= 1) {
      pairTakes.push(1);
    }
    for (let takeIndex = 0; takeIndex < pairTakes.length; takeIndex += 1) {
      const take = pairTakes[takeIndex];
      const need = 2 - take;
      if (need > wildcards) {
        continue;
      }
      const nextTuple = tuple.slice();
      nextTuple[index] -= take;
      if (canFormMelds(nextTuple, wildcards - need, setsNeeded)) {
        return true;
      }
    }
  }

  if (wildcards >= 2 && canFormMelds(tuple, wildcards - 2, setsNeeded)) {
    return true;
  }
  return false;
}

function countTiles(tiles) {
  return tiles.reduce((counts, tile) => {
    counts[tile] = (counts[tile] || 0) + 1;
    return counts;
  }, {});
}

function countsTuple(counts) {
  return PLAYABLE_TILES.map((tile) => counts[tile] || 0);
}

const meldMemo = {};

function canFormMelds(tuple, wildcards, setsNeeded) {
  const key = `${tuple.join(",")}|${wildcards}|${setsNeeded}`;
  if (Object.prototype.hasOwnProperty.call(meldMemo, key)) {
    return meldMemo[key];
  }
  if (setsNeeded === 0) {
    const ok = tuple.reduce((sum, count) => sum + count, 0) === 0;
    meldMemo[key] = ok;
    return ok;
  }
  const first = tuple.findIndex((count) => count > 0);
  if (first < 0) {
    const ok = wildcards >= setsNeeded * 3;
    meldMemo[key] = ok;
    return ok;
  }

  const tripletTake = Math.min(3, tuple[first]);
  const tripletNeed = 3 - tripletTake;
  if (tripletNeed <= wildcards) {
    const nextTuple = tuple.slice();
    nextTuple[first] -= tripletTake;
    if (canFormMelds(nextTuple, wildcards - tripletNeed, setsNeeded - 1)) {
      meldMemo[key] = true;
      return true;
    }
  }

  if (canMakeSequenceFrom(first)) {
    const indexes = [first, first + 1, first + 2];
    const sequenceNeed = indexes.filter((index) => tuple[index] === 0).length;
    if (sequenceNeed <= wildcards) {
      const nextTuple = tuple.slice();
      indexes.forEach((index) => {
        if (nextTuple[index] > 0) {
          nextTuple[index] -= 1;
        }
      });
      if (canFormMelds(nextTuple, wildcards - sequenceNeed, setsNeeded - 1)) {
        meldMemo[key] = true;
        return true;
      }
    }
  }

  meldMemo[key] = false;
  return false;
}

function canMakeSequenceFrom(index) {
  const tile = PLAYABLE_TILES[index];
  if (!isNumbered(tile)) {
    return false;
  }
  return tileNumber(tile) <= 7 && PLAYABLE_TILES[index + 1].slice(0, 1) === tile.slice(0, 1);
}

module.exports = {
  countGold,
  evaluateWin,
  evaluateQiangjin,
  findYoujinDiscard,
  isSevenPairs,
  isThirteenOrphans,
  isStandardWin,
};
