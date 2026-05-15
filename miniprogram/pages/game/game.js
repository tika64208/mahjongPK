let MiniMahjongGame = null;

Page({
  data: emptySnapshot(),
  selectedTileIndex: null,

  onLoad() {
    this.game = null;
  },

  onNewRound() {
    this.selectedTileIndex = null;
    this.ensureGame();
    this.refresh();
    this.startRoundAsync();
  },

  ensureGame() {
    if (!MiniMahjongGame) {
      MiniMahjongGame = require("../../core/game").MiniMahjongGame;
    }
    this.game = new MiniMahjongGame(false);
  },

  startRoundAsync() {
    this.setData({
      statusText: "洗牌中",
      logs: ["正在准备新一局..."],
    });
    setTimeout(() => {
      this.game.prepareRound();
      this.refresh();
      setTimeout(() => {
        this.game.startPreparedRound();
        this.refresh();
      }, 0);
    }, 0);
  },

  onSelectTile(event) {
    if (!this.game) {
      return;
    }
    const index = event.currentTarget.dataset.index;
    const snapshot = this.game.snapshot();
    if (!snapshot.canDiscard) {
      return;
    }
    this.selectedTileIndex = this.selectedTileIndex === index ? null : index;
    this.refresh();
  },

  onHumanWin() {
    if (!this.game) {
      return;
    }
    this.selectedTileIndex = null;
    this.game.humanWin();
    this.refresh();
  },

  onHumanYoujin() {
    if (!this.game) {
      return;
    }
    this.selectedTileIndex = null;
    this.game.humanYoujin();
    this.refresh();
  },

  onHumanSelfKong(event) {
    if (!this.game) {
      return;
    }
    const index = event.currentTarget.dataset.index;
    this.selectedTileIndex = null;
    this.game.humanSelfKong(index);
    this.refresh();
  },

  onConfirmDiscard() {
    if (!this.game || this.selectedTileIndex === null) {
      return;
    }
    const index = this.selectedTileIndex;
    this.selectedTileIndex = null;
    this.game.humanDiscard(index);
    this.refresh();
  },

  onCancelSelection() {
    this.selectedTileIndex = null;
    this.refresh();
  },

  onHumanPong() {
    if (!this.game) {
      return;
    }
    this.selectedTileIndex = null;
    this.game.humanPong();
    this.refresh();
  },

  onHumanExposedKong() {
    if (!this.game) {
      return;
    }
    this.selectedTileIndex = null;
    this.game.humanExposedKong();
    this.refresh();
  },

  onPassReaction() {
    if (!this.game) {
      return;
    }
    this.selectedTileIndex = null;
    this.game.passReaction();
    this.refresh();
  },

  refresh() {
    const snapshot = this.game ? this.game.snapshot() : emptySnapshot();
    if (
      !snapshot.canDiscard ||
      this.selectedTileIndex === null ||
      this.selectedTileIndex >= snapshot.humanHand.length
    ) {
      this.selectedTileIndex = null;
    }
    const selectedTile = this.selectedTileIndex === null
      ? null
      : snapshot.humanHand[this.selectedTileIndex];
    snapshot.humanHand = snapshot.humanHand.map((tile, index) => ({
      ...tile,
      selected: index === this.selectedTileIndex,
    }));
    snapshot.selectedTileIndex = this.selectedTileIndex;
    snapshot.selectedTileText = selectedTile ? selectedTile.display : "";
    snapshot.canConfirmDiscard = snapshot.canDiscard && this.selectedTileIndex !== null;
    this.setData(snapshot);
  },
});

function emptySnapshot() {
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
    youjinDiscardText: "",
    selfKongOptions: [],
    pendingReaction: false,
    reactionTileText: "",
    reactionSourceName: "",
    reactionTileGroup: "",
    canHumanKong: false,
    canHumanPong: false,
    roundOver: false,
    resultText: "",
    scoreText: "",
    logs: ["点击开始进入一局。"],
    roundStarted: false,
    selectedTileIndex: null,
    selectedTileText: "",
    canConfirmDiscard: false,
  };
}
