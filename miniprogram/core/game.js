const {
  PLAYABLE_TILES,
  TILE_INDEX,
  buildWall,
  displayTile,
  displayTiles,
  isFlower,
  sortTiles,
} = require("./tiles");
const {
  countGold,
  evaluateQiangjin,
  evaluateWin,
  findYoujinDiscard,
} = require("./evaluator");
const bot = require("./bot");

const HUMAN_INDEX = 0;

class MiniMahjongGame {
  constructor(autoStart = true) {
    this.players = [];
    this.wall = [];
    this.discards = [];
    this.goldTile = null;
    this.dealer = 0;
    this.current = 0;
    this.firstTurn = true;
    this.discardOnly = false;
    this.preparedDrawn = null;
    this.preparedDrawnFromKong = false;
    this.lastDrawFromKong = false;
    this.logs = [];
    this.pendingReaction = null;
    this.roundOver = false;
    this.resultText = "";
    this.scoreText = "";
    if (autoStart) {
      this.newRound();
    }
  }

  newRound() {
    this.players = [
      createPlayer("你", true),
      createPlayer("机器人A", false),
      createPlayer("机器人B", false),
      createPlayer("机器人C", false),
    ];
    this.wall = shuffle(buildWall(true));
    this.goldTile = this.popGoldTile();
    this.discards = [];
    this.current = this.dealer;
    this.firstTurn = true;
    this.discardOnly = false;
    this.preparedDrawn = null;
    this.preparedDrawnFromKong = false;
    this.lastDrawFromKong = false;
    this.pendingReaction = null;
    this.roundOver = false;
    this.resultText = "";
    this.scoreText = "";
    this.logs = [`开局，金牌 ${displayTile(this.goldTile)}`];

    for (let round = 0; round < 13; round += 1) {
      this.players.forEach((player) => this.drawHandTile(player, false));
    }
    this.drawHandTile(this.players[this.dealer], false);
    this.players.forEach((player) => {
      player.hand = sortTiles(player.hand);
      player.latestDrawnTile = null;
      if (player.flowers.length) {
        this.log(`${player.name} 起手补花 ${displayTiles(player.flowers)}`);
      }
    });

    this.checkOpeningSpecialWin();
    if (!this.roundOver) {
      this.advanceUntilHumanDecision();
    }
  }

  prepareRound() {
    this.players = [
      createPlayer("你", true),
      createPlayer("机器人A", false),
      createPlayer("机器人B", false),
      createPlayer("机器人C", false),
    ];
    this.wall = shuffle(buildWall(true));
    this.goldTile = this.popGoldTile();
    this.discards = [];
    this.current = this.dealer;
    this.firstTurn = true;
    this.discardOnly = false;
    this.preparedDrawn = null;
    this.preparedDrawnFromKong = false;
    this.lastDrawFromKong = false;
    this.pendingReaction = null;
    this.roundOver = false;
    this.resultText = "";
    this.scoreText = "";
    this.logs = [`开局，金牌 ${displayTile(this.goldTile)}`];

    for (let round = 0; round < 13; round += 1) {
      this.players.forEach((player) => this.drawHandTile(player, false));
    }
    this.drawHandTile(this.players[this.dealer], false);
    this.players.forEach((player) => {
      player.hand = sortTiles(player.hand);
      player.latestDrawnTile = null;
      if (player.flowers.length) {
        this.log(`${player.name} 起手补花 ${displayTiles(player.flowers)}`);
      }
    });
  }

  startPreparedRound() {
    this.checkOpeningSpecialWin();
    if (!this.roundOver) {
      this.advanceUntilHumanDecision();
    }
  }

  advanceUntilHumanDecision() {
    if (this.roundOver) {
      return;
    }
    let guard = 0;
    while (!this.roundOver && !this.pendingReaction && this.wall.length >= 0 && guard < 500) {
      guard += 1;
      const player = this.players[this.current];

      if (player.isHuman && this.discardOnly) {
        return;
      }

      if (!this.discardOnly) {
        const drawn = this.consumePreparedOrDraw(player);
        if (drawn === null && !this.firstTurn) {
          this.finishDraw();
          return;
        }

        if (player.youjinLevel) {
          if (this.applyYoujinDraw(player, drawn)) {
            this.nextPlayer();
            continue;
          }
          const win = player.youjinLevel === 1
            ? { kind: "single_you", label: "单游", multiplier: 5 }
            : { kind: "double_you", label: "双游", multiplier: 10 };
          this.finishWin(this.current, win);
          return;
        }

        let win = evaluateWin(player.hand, this.goldTile, player.melds.length);
        if (win && this.lastDrawFromKong) {
          win = applyKongBloom(win);
        }
        if (win) {
          if (player.isHuman) {
            return;
          }
          const youjinDiscard = findYoujinDiscard(player.hand, this.goldTile, player.melds.length);
          if (youjinDiscard) {
            removeTile(player.hand, youjinDiscard);
            player.youjinLevel = 1;
            this.log(`${player.name} 打出 ${displayTile(youjinDiscard)}，进入单游`);
            this.nextPlayer();
            continue;
          }
          this.finishWin(this.current, win);
          return;
        }

        const selfKong = this.chooseBotSelfKong(player);
        if (selfKong) {
          this.performSelfKong(player, selfKong.kind, selfKong.tile);
          continue;
        }
      }

      if (player.isHuman) {
        return;
      }

      const discarded = this.botDiscard(player);
      if (this.applyYoujinGoldDiscard(this.current, discarded)) {
        this.nextPlayer();
        continue;
      }
      this.resolveDiscardReactions(discarded);
    }
  }

  applyYoujinGoldDiscard(playerIndex, tile) {
    const player = this.players[playerIndex];
    if (player.youjinLevel === 1 && tile === this.goldTile) {
      player.youjinLevel = 2;
      player.latestDrawnTile = null;
      this.discardOnly = false;
      this.log(`${player.name} 进入双游`);
      return true;
    }
    return false;
  }

  applyYoujinDraw(player, drawn) {
    if (player.youjinLevel === 1 && drawn === this.goldTile) {
      removeTile(player.hand, this.goldTile);
      player.youjinLevel = 2;
      this.log(`${player.name} 摸到金牌，进入双游`);
      return true;
    }
    return false;
  }

  humanDiscard(index) {
    if (this.roundOver || this.pendingReaction || this.current !== HUMAN_INDEX) {
      return;
    }
    const player = this.players[HUMAN_INDEX];
    const tile = player.hand.splice(index, 1)[0];
    player.hand = sortTiles(player.hand);
    player.latestDrawnTile = null;
    this.log(`${player.name} 打出 ${displayTile(tile)}`);
    this.discards.push({ player: HUMAN_INDEX, tile });
    if (this.applyYoujinGoldDiscard(HUMAN_INDEX, tile)) {
      this.nextPlayer();
      this.advanceUntilHumanDecision();
      return;
    }
    this.resolveDiscardReactions(tile);
    this.advanceUntilHumanDecision();
  }

  humanWin() {
    const player = this.players[HUMAN_INDEX];
    let win = evaluateWin(player.hand, this.goldTile, player.melds.length);
    if (win && this.lastDrawFromKong) {
      win = applyKongBloom(win);
    }
    if (win) {
      this.finishWin(HUMAN_INDEX, win);
    }
  }

  humanYoujin() {
    const player = this.players[HUMAN_INDEX];
    const tile = findYoujinDiscard(player.hand, this.goldTile, player.melds.length);
    if (!tile) {
      return;
    }
    removeTile(player.hand, tile);
    player.youjinLevel = 1;
    player.latestDrawnTile = null;
    this.log(`${player.name} 打出 ${displayTile(tile)}，进入单游`);
    this.nextPlayer();
    this.advanceUntilHumanDecision();
  }

  humanSelfKong(index) {
    const options = this.availableSelfKongs(this.players[HUMAN_INDEX]);
    const option = options[index];
    if (!option) {
      return;
    }
    this.performSelfKong(this.players[HUMAN_INDEX], option.kind, option.tile);
    this.advanceUntilHumanDecision();
  }

  humanPong() {
    if (!this.pendingReaction || !this.pendingReaction.canPong) {
      return;
    }
    const tile = this.pendingReaction.tile;
    const source = this.pendingReaction.source;
    const player = this.players[HUMAN_INDEX];
    removeCopies(player.hand, tile, 2);
    player.melds.push({ kind: "pong", tiles: [tile, tile, tile], source });
    this.removeLastDiscard(tile, source);
    this.log(`${player.name} 碰 ${displayTile(tile)}`);
    this.current = HUMAN_INDEX;
    this.discardOnly = true;
    this.pendingReaction = null;
  }

  humanExposedKong() {
    if (!this.pendingReaction || !this.pendingReaction.canKong) {
      return;
    }
    const tile = this.pendingReaction.tile;
    const source = this.pendingReaction.source;
    const player = this.players[HUMAN_INDEX];
    removeCopies(player.hand, tile, 3);
    player.melds.push({ kind: "exposed_kong", tiles: [tile, tile, tile, tile], source });
    this.removeLastDiscard(tile, source);
    this.log(`${player.name} 明杠 ${displayTile(tile)}`);
    this.applyKongScore("exposed", HUMAN_INDEX, source);
    this.current = HUMAN_INDEX;
    this.discardOnly = false;
    this.pendingReaction = null;
    this.preparedDrawn = this.drawHandTile(player, true);
    this.preparedDrawnFromKong = true;
    this.advanceUntilHumanDecision();
  }

  passReaction() {
    if (!this.pendingReaction) {
      return;
    }
    const source = this.pendingReaction.source;
    this.pendingReaction = null;
    this.current = (source + 1) % 4;
    this.discardOnly = false;
    this.advanceUntilHumanDecision();
  }

  checkOpeningSpecialWin() {
    const order = [0, 1, 2, 3];
    for (let index = 0; index < order.length; index += 1) {
      const playerIndex = order[index];
      const player = this.players[playerIndex];
      if (countGold(player.hand, this.goldTile) >= 3) {
        this.finishWin(playerIndex, { kind: "three_gold", label: "三金倒", multiplier: 3 });
        return;
      }
    }
    const qiangjinOrder = [1, 2, 3, 0];
    for (let index = 0; index < qiangjinOrder.length; index += 1) {
      const playerIndex = qiangjinOrder[index];
      const player = this.players[playerIndex];
      const win = evaluateQiangjin(player.hand, this.goldTile);
      if (win) {
        this.finishWin(playerIndex, win);
        return;
      }
    }
  }

  consumePreparedOrDraw(player) {
    if (this.preparedDrawn) {
      const drawn = this.preparedDrawn;
      this.preparedDrawn = null;
      this.lastDrawFromKong = this.preparedDrawnFromKong;
      this.preparedDrawnFromKong = false;
      return drawn;
    }
    this.lastDrawFromKong = false;
    if (this.firstTurn && this.current === this.dealer) {
      this.firstTurn = false;
      return undefined;
    }
    const drawn = this.drawHandTile(player, true);
    if (drawn) {
      this.log(`${player.name} 摸牌`);
    }
    return drawn;
  }

  botDiscard(player) {
    const tile = bot.chooseDiscard(player.hand, this.goldTile);
    removeTile(player.hand, tile);
    player.latestDrawnTile = null;
    this.log(`${player.name} 打出 ${displayTile(tile)}`);
    this.discards.push({ player: this.current, tile });
    return tile;
  }

  resolveDiscardReactions(tile) {
    const source = this.current;
    const human = this.players[HUMAN_INDEX];
    if (source !== HUMAN_INDEX) {
      const humanCanKong = canExposedKong(human, tile, this.goldTile);
      const humanCanPong = canPong(human, tile, this.goldTile);
      if (humanCanKong || humanCanPong) {
        this.pendingReaction = {
          tile,
          source,
          sourceName: this.players[source].name,
          canKong: humanCanKong,
          canPong: humanCanPong,
        };
        return;
      }
    }

    const kongPlayer = this.findBotExposedKongPlayer(tile, source);
    if (kongPlayer !== null) {
      const player = this.players[kongPlayer];
      removeCopies(player.hand, tile, 3);
      player.melds.push({ kind: "exposed_kong", tiles: [tile, tile, tile, tile], source });
      this.removeLastDiscard(tile, source);
      this.log(`${player.name} 明杠 ${displayTile(tile)}`);
      this.applyKongScore("exposed", kongPlayer, source);
      this.current = kongPlayer;
      this.discardOnly = false;
      this.preparedDrawn = this.drawHandTile(player, true);
      this.preparedDrawnFromKong = true;
      return;
    }

    const pongPlayer = this.findBotPongPlayer(tile, source);
    if (pongPlayer !== null) {
      const player = this.players[pongPlayer];
      removeCopies(player.hand, tile, 2);
      player.melds.push({ kind: "pong", tiles: [tile, tile, tile], source });
      this.removeLastDiscard(tile, source);
      this.log(`${player.name} 碰 ${displayTile(tile)}`);
      this.current = pongPlayer;
      this.discardOnly = true;
      return;
    }

    this.current = (source + 1) % 4;
    this.discardOnly = false;
  }

  findBotExposedKongPlayer(tile, source) {
    for (let offset = 1; offset < 4; offset += 1) {
      const index = (source + offset) % 4;
      if (index === HUMAN_INDEX) {
        continue;
      }
      const player = this.players[index];
      if (canExposedKong(player, tile, this.goldTile) && bot.wantsExposedKong(player.hand, tile, this.goldTile)) {
        return index;
      }
    }
    return null;
  }

  findBotPongPlayer(tile, source) {
    for (let offset = 1; offset < 4; offset += 1) {
      const index = (source + offset) % 4;
      if (index === HUMAN_INDEX) {
        continue;
      }
      const player = this.players[index];
      if (canPong(player, tile, this.goldTile) && bot.wantsPong(player.hand, tile, this.goldTile)) {
        return index;
      }
    }
    return null;
  }

  chooseBotSelfKong(player) {
    if (player.isHuman) {
      return null;
    }
    const options = this.availableSelfKongs(player);
    return options.find((option) => bot.wantsSelfKong(player.hand, option.tile, this.goldTile)) || null;
  }

  availableSelfKongs(player) {
    const options = [];
    const seen = {};
    player.hand.forEach((tile) => {
      if (!seen[tile] && canConcealedKong(player, tile, this.goldTile)) {
        options.push({ kind: "concealed", tile, label: `暗杠 ${displayTile(tile)}` });
        seen[tile] = true;
      }
    });
    player.melds.forEach((meld) => {
      const tile = meld.tiles[0];
      if (meld.kind === "pong" && player.hand.indexOf(tile) >= 0 && tile !== this.goldTile) {
        options.push({ kind: "added", tile, label: `补杠 ${displayTile(tile)}` });
      }
    });
    return options;
  }

  performSelfKong(player, kind, tile) {
    if (kind === "concealed") {
      removeCopies(player.hand, tile, 4);
      player.melds.push({ kind: "concealed_kong", tiles: [tile, tile, tile, tile], source: this.current });
      this.log(`${player.name} 暗杠 ${displayTile(tile)}`);
      this.applyKongScore("concealed", this.current, null);
    } else {
      if (this.resolveRobKong(this.current, tile)) {
        return;
      }
      removeTile(player.hand, tile);
      const meld = player.melds.find((item) => item.kind === "pong" && item.tiles[0] === tile);
      if (meld) {
        meld.kind = "added_kong";
        meld.tiles = [tile, tile, tile, tile];
      }
      this.log(`${player.name} 补杠 ${displayTile(tile)}`);
      this.applyKongScore("added", this.current, null);
    }
    this.preparedDrawn = this.drawHandTile(player, true);
    this.preparedDrawnFromKong = true;
    this.discardOnly = false;
  }

  resolveRobKong(kongerIndex, tile) {
    for (let offset = 1; offset < 4; offset += 1) {
      const index = (kongerIndex + offset) % 4;
      const player = this.players[index];
      if (player.youjinLevel) {
        continue;
      }
      const win = evaluateWin(player.hand.concat([tile]), this.goldTile, player.melds.length);
      if (win) {
        this.log(`${player.name} 抢杠胡 ${displayTile(tile)}`);
        this.finishWin(index, { kind: "rob_kong", label: "抢杠胡", multiplier: win.multiplier }, { payer: kongerIndex });
        return true;
      }
    }
    return false;
  }

  applyKongScore(kind, kongPlayer, sourcePlayer) {
    const score = scoreKong(kind, kongPlayer, this.dealer, sourcePlayer);
    this.players.forEach((player, index) => {
      player.score += score.payments[index];
    });
    const text = score.payments.map((payment, index) => `${this.players[index].name}${payment >= 0 ? "+" : ""}${payment}`).join(" ");
    this.log(`${score.label}得分：${text}`);
    return score;
  }

  drawHandTile(player, logFlowers) {
    while (this.wall.length) {
      const tile = this.wall.pop();
      if (isFlower(tile)) {
        player.flowers.push(tile);
        if (logFlowers) {
          this.log(`${player.name} 补花 ${displayTile(tile)}`);
        }
        continue;
      }
      player.hand.push(tile);
      player.hand = sortTiles(player.hand);
      player.latestDrawnTile = logFlowers ? tile : null;
      return tile;
    }
    return null;
  }

  popGoldTile() {
    for (let index = this.wall.length - 1; index >= 0; index -= 1) {
      const tile = this.wall[index];
      if (!isFlower(tile)) {
        this.wall.splice(index, 1);
        return tile;
      }
    }
    return PLAYABLE_TILES[0];
  }

  removeLastDiscard(tile, source) {
    for (let index = this.discards.length - 1; index >= 0; index -= 1) {
      const discard = this.discards[index];
      if (discard.tile === tile && discard.player === source) {
        this.discards.splice(index, 1);
        return;
      }
    }
  }

  nextPlayer() {
    this.current = (this.current + 1) % 4;
    this.discardOnly = false;
  }

  finishWin(winner, win, options = {}) {
    const score = options.payer === undefined
      ? scoreSelfDraw(winner, this.dealer, win)
      : scoreRobKong(winner, options.payer, this.dealer, win);
    this.players.forEach((player, index) => {
      player.score += score.payments[index];
    });
    this.roundOver = true;
    this.current = winner;
    this.resultText = `${this.players[winner].name} 胡牌：${score.label}`;
    this.scoreText = score.payments.map((payment, index) => `${this.players[index].name}${payment >= 0 ? "+" : ""}${payment}`).join(" ");
    this.log(`${this.resultText}，${this.scoreText}`);
  }

  finishDraw() {
    this.roundOver = true;
    this.resultText = "流局";
    this.scoreText = "牌墙摸完";
    this.log("牌墙摸完，流局");
  }

  log(message) {
    this.logs.unshift(message);
    if (this.logs.length > 80) {
      this.logs = this.logs.slice(0, 80);
    }
  }

  snapshot() {
    if (!this.players.length || !this.goldTile) {
      return {
        goldDisplay: "-",
        wallRemaining: 0,
        currentPlayerName: "-",
        statusText: "准备中",
        players: [],
        humanHand: [],
        humanFlowers: [],
        humanTurn: false,
        canDiscard: false,
        canHumanWin: false,
        canHumanYoujin: false,
        selfKongOptions: [],
        pendingReaction: false,
        canHumanKong: false,
        canHumanPong: false,
        roundOver: false,
        resultText: "",
        scoreText: "",
        logs: this.logs || [],
        roundStarted: false,
      };
    }
    const human = this.players[HUMAN_INDEX];
    const win = evaluateWin(human.hand, this.goldTile, human.melds.length);
    const youjinDiscard = findYoujinDiscard(human.hand, this.goldTile, human.melds.length);
    return {
      goldDisplay: displayTile(this.goldTile),
      wallRemaining: this.wall.length,
      currentPlayerName: this.players[this.current].name,
      statusText: this.roundOver
        ? "本局结束"
        : this.pendingReaction
          ? `是否响应 ${displayTile(this.pendingReaction.tile)}`
          : this.current === HUMAN_INDEX
            ? "轮到你操作"
            : "机器人思考中",
      players: this.players.map((player, index) => ({
        name: player.name,
        score: player.score,
        handCount: player.isHuman ? player.hand.length : player.hand.length,
        meldCount: player.melds.length,
        flowers: player.flowers.length,
        youjinLabel: youjinLabel(player.youjinLevel),
        discards: this.discardsForPlayer(index),
        melds: player.melds.map((meld, meldIndex) => meldSnapshot(meld, meldIndex)),
        active: index === this.current,
        human: player.isHuman,
      })),
      humanHand: this.humanHandSnapshot(human),
      humanFlowers: human.flowers.map((tile, index) => ({
        key: `${tile}-${index}`,
        tile,
        display: displayTile(tile),
        group: "flower",
      })),
      humanTurn: this.current === HUMAN_INDEX && !this.pendingReaction,
      canDiscard: this.current === HUMAN_INDEX && !this.roundOver && !this.pendingReaction,
      canHumanWin: Boolean(win),
      canHumanYoujin: Boolean(win && youjinDiscard),
      youjinDiscardText: youjinDiscard ? displayTile(youjinDiscard) : "",
      selfKongOptions: this.availableSelfKongs(human).map((option, index) => ({
        key: `${option.kind}-${option.tile}-${index}`,
        label: option.label,
      })),
      pendingReaction: Boolean(this.pendingReaction),
      reactionTileText: this.pendingReaction ? displayTile(this.pendingReaction.tile) : "",
      reactionSourceName: this.pendingReaction ? this.pendingReaction.sourceName : "",
      reactionTileGroup: this.pendingReaction ? tileGroup(this.pendingReaction.tile) : "",
      canHumanKong: Boolean(this.pendingReaction && this.pendingReaction.canKong),
      canHumanPong: Boolean(this.pendingReaction && this.pendingReaction.canPong),
      roundOver: this.roundOver,
      resultText: this.resultText,
      scoreText: this.scoreText,
      logs: this.logs,
      roundStarted: true,
    };
  }

  humanHandSnapshot(human) {
    const latestIndex = human.latestDrawnTile ? human.hand.lastIndexOf(human.latestDrawnTile) : -1;
    const reactionTile = this.pendingReaction ? this.pendingReaction.tile : null;
    return human.hand.map((tile, index) => ({
      key: `${tile}-${index}`,
      tile,
      display: displayTile(tile),
      group: tileGroup(tile),
      gold: tile === this.goldTile,
      latest: index === latestIndex,
      reactionMatch: tile === reactionTile,
    }));
  }

  discardsForPlayer(playerIndex) {
    return this.discards
      .filter((discard) => discard.player === playerIndex)
      .map((discard, index) => ({
        key: `${discard.tile}-${index}`,
        tile: discard.tile,
        display: displayTile(discard.tile),
      }));
  }
}

function createPlayer(name, isHuman) {
  return {
    name,
    isHuman,
    hand: [],
    melds: [],
    flowers: [],
    youjinLevel: 0,
    latestDrawnTile: null,
    score: 0,
  };
}

function shuffle(items) {
  const next = items.slice();
  for (let index = next.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    const tmp = next[index];
    next[index] = next[randomIndex];
    next[randomIndex] = tmp;
  }
  return next;
}

function removeTile(tiles, tile) {
  const index = tiles.indexOf(tile);
  if (index >= 0) {
    tiles.splice(index, 1);
  }
  tiles.sort((left, right) => TILE_INDEX[left] - TILE_INDEX[right]);
}

function removeCopies(tiles, tile, copies) {
  for (let count = 0; count < copies; count += 1) {
    removeTile(tiles, tile);
  }
}

function canPong(player, tile, goldTile) {
  return tile !== goldTile && bot.countTile(player.hand, tile) >= 2;
}

function canExposedKong(player, tile, goldTile) {
  return tile !== goldTile && bot.countTile(player.hand, tile) >= 3;
}

function canConcealedKong(player, tile, goldTile) {
  return tile !== goldTile && bot.countTile(player.hand, tile) >= 4;
}

function applyKongBloom(win) {
  return {
    kind: "kong_bloom",
    label: "杠上开花",
    multiplier: Math.max(win.multiplier + 1, 2),
  };
}

function scoreSelfDraw(winner, dealer, win) {
  const multiplier = win.multiplier;
  const payments = [0, 0, 0, 0];
  for (let index = 0; index < 4; index += 1) {
    if (index === winner) {
      continue;
    }
    let amount = multiplier;
    if (winner === dealer || index === dealer) {
      amount *= 2;
    }
    payments[index] = -amount;
    payments[winner] += amount;
  }
  return { label: win.label, payments };
}

function scoreRobKong(winner, payer, dealer, win) {
  const base = scoreSelfDraw(winner, dealer, win);
  const payments = [0, 0, 0, 0];
  const gain = base.payments[winner];
  payments[winner] = gain;
  payments[payer] = -gain;
  return { label: "抢杠胡", payments };
}

function scoreKong(kind, kongPlayer, dealer, sourcePlayer) {
  const multiplier = kind === "concealed" ? 2 : 1;
  const payments = [0, 0, 0, 0];
  for (let index = 0; index < 4; index += 1) {
    if (index === kongPlayer) {
      continue;
    }
    let amount = multiplier;
    if (kongPlayer === dealer || index === dealer) {
      amount *= 2;
    }
    payments[index] = -amount;
    payments[kongPlayer] += amount;
  }
  if (sourcePlayer !== null && sourcePlayer !== undefined) {
    const total = payments[kongPlayer];
    payments.fill(0);
    payments[kongPlayer] = total;
    payments[sourcePlayer] = -total;
  }
  const labels = {
    exposed: "明杠",
    concealed: "暗杠",
    added: "补杠",
  };
  return { label: labels[kind] || "杠", payments };
}

function tileGroup(tile) {
  if (tile.indexOf("M") === 0) {
    return "m";
  }
  if (tile.indexOf("T") === 0) {
    return "t";
  }
  if (tile.indexOf("S") === 0) {
    return "s";
  }
  return "honor";
}

function youjinLabel(level) {
  if (level === 1) {
    return "单游";
  }
  if (level === 2) {
    return "双游";
  }
  return "";
}

function meldSnapshot(meld, index) {
  return {
    key: `${meld.kind}-${meld.tiles.join("-")}-${index}`,
    kind: meld.kind,
    label: meldLabel(meld.kind),
    tiles: meld.tiles.map((tile, tileIndex) => ({
      key: `${tile}-${tileIndex}`,
      display: displayTile(tile),
    })),
  };
}

function meldLabel(kind) {
  if (kind === "pong") {
    return "碰";
  }
  if (kind === "exposed_kong") {
    return "明杠";
  }
  if (kind === "concealed_kong") {
    return "暗杠";
  }
  if (kind === "added_kong") {
    return "补杠";
  }
  return "副露";
}

module.exports = {
  MiniMahjongGame,
};
