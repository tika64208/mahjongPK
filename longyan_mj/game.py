"""Round runner for local Longyan Mahjong games."""

import random
from typing import Callable, List, Optional

from .bot import BotPolicy, default_bot_policies
from .evaluator import WinResult, evaluate_win
from .rules import LONGYAN_HALF_SELF_DRAW, RuleProfile
from .scoring import ScoreResult, score_self_draw
from .state import Player
from .tiles import build_wall, display_tile, display_tiles, sort_tiles

InputFunc = Callable[[str], str]
OutputFunc = Callable[[str], None]


class GameResult:
    def __init__(
        self,
        winner: Optional[int],
        win: Optional[WinResult],
        reason: str,
        score: Optional[ScoreResult] = None,
    ) -> None:
        self.winner = winner
        self.win = win
        self.reason = reason
        self.score = score


class MahjongGame:
    def __init__(
        self,
        rules: RuleProfile = LONGYAN_HALF_SELF_DRAW,
        seed: Optional[int] = None,
        human_index: int = 0,
        bot_policies: Optional[List[BotPolicy]] = None,
    ) -> None:
        self.rules = rules
        self.random = random.Random(seed)
        self.human_index = human_index
        self.players: List[Player] = [
            Player("你", is_human=True),
            Player("机器人A"),
            Player("机器人B"),
            Player("机器人C"),
        ]
        self.bots = bot_policies or default_bot_policies()
        self.wall: List[str] = []
        self.discards: List[str] = []
        self.gold_tile: Optional[str] = None
        self.dealer = 0
        self.current = self.dealer

    def start_round(self) -> None:
        self.wall = build_wall()
        self.random.shuffle(self.wall)
        self.gold_tile = self.wall.pop()
        self.discards = []
        self.current = self.dealer
        for player in self.players:
            player.hand.clear()
            player.melds.clear()
        for _ in range(13):
            for player in self.players:
                player.hand.append(self.wall.pop())
        self.players[self.dealer].hand.append(self.wall.pop())
        for player in self.players:
            player.sort_hand()

    def play(self, input_func: InputFunc = input, output_func: OutputFunc = print) -> GameResult:
        self.start_round()
        output_func(f"本局规则：{self.rules.name}")
        output_func(f"金牌：{display_tile(self.gold_tile)}")
        output_func("机器人能力：" + "，".join(bot.name for bot in self.bots))
        output_func("牌局开始。输入手牌编号出牌，输入 q 可退出。")

        first_turn = True
        discard_only = False

        while self.wall:
            player = self.players[self.current]

            if not discard_only:
                if first_turn and self.current == self.dealer:
                    first_turn = False
                else:
                    drawn = self.wall.pop()
                    player.hand.append(drawn)
                    player.sort_hand()
                    if player.is_human:
                        output_func(f"\n你摸到：{display_tile(drawn)}")
                    else:
                        output_func(f"\n{player.name} 摸牌")

                win = evaluate_win(player.hand, self.gold_tile, open_melds=len(player.melds))
                if win and self._accept_win(player, win, input_func, output_func):
                    score = score_self_draw(self.current, self.dealer, win)
                    output_func(
                        f"{player.name} 胡牌：{score.win_label}，"
                        f"{score.multiplier} 倍，得分 +{score.total_gain}，"
                        f"手牌 {display_tiles(player.hand)}"
                    )
                    output_func(self._format_score_payments(score))
                    return GameResult(self.current, win, "win", score=score)

            discarded = self._discard(player, input_func, output_func)
            self.discards.append(discarded)
            output_func(f"{player.name} 打出：{display_tile(discarded)}")

            pong_player = self._find_pong_player(discarded, input_func, output_func)
            if pong_player is not None:
                self.players[pong_player].pong(discarded, self.current)
                output_func(f"{self.players[pong_player].name} 碰 {display_tile(discarded)}")
                self.current = pong_player
                discard_only = True
                continue

            self.current = (self.current + 1) % 4
            discard_only = False

        output_func("牌墙摸完，流局。")
        return GameResult(None, None, "draw")

    def _accept_win(
        self, player: Player, win: WinResult, input_func: InputFunc, output_func: OutputFunc
    ) -> bool:
        if not player.is_human:
            return True
        output_func(f"你的手牌：{self._numbered_hand(player)}")
        while True:
            answer = input_func(f"可胡牌（{win.label}），是否胡？[y/n] ").strip().lower()
            if answer in ("y", "yes", "h", "hu", "胡"):
                return True
            if answer in ("n", "no", ""):
                return False
            output_func("请输入 y 或 n。")

    def _discard(self, player: Player, input_func: InputFunc, output_func: OutputFunc) -> str:
        if player.is_human:
            return self._human_discard(player, input_func, output_func)
        tile = self._bot_for_player(self.current).choose_discard(
            player.hand, self.gold_tile, open_melds=len(player.melds)
        )
        return player.remove_tile(tile)

    def _human_discard(self, player: Player, input_func: InputFunc, output_func: OutputFunc) -> str:
        while True:
            output_func(f"你的手牌：{self._numbered_hand(player)}")
            answer = input_func("请选择要打出的牌编号：").strip().lower()
            if answer in ("q", "quit", "exit"):
                raise KeyboardInterrupt("玩家退出牌局")
            if not answer.isdigit():
                output_func("请输入手牌编号。")
                continue
            index = int(answer) - 1
            if 0 <= index < len(player.hand):
                return player.remove_tile_at(index)
            output_func("编号超出范围。")

    def _find_pong_player(
        self, discarded: str, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[int]:
        if not self.rules.allow_pong:
            return None
        for offset in range(1, 4):
            index = (self.current + offset) % 4
            player = self.players[index]
            if not player.can_pong(discarded, self.gold_tile):
                continue
            if player.is_human:
                output_func(f"你的手牌：{self._numbered_hand(player)}")
                answer = input_func(f"是否碰 {display_tile(discarded)}？[y/n] ").strip().lower()
                if answer in ("y", "yes", "p", "peng", "碰"):
                    return index
            elif self._bot_for_player(index).wants_pong(
                player.hand, discarded, self.gold_tile, open_melds=len(player.melds)
            ):
                return index
        return None

    def _bot_for_player(self, player_index: int) -> BotPolicy:
        bot_index = player_index - 1 if player_index > self.human_index else player_index
        return self.bots[bot_index % len(self.bots)]

    def _numbered_hand(self, player: Player) -> str:
        player.hand = sort_tiles(player.hand)
        parts = []
        for index, tile in enumerate(player.hand, start=1):
            marker = "*" if tile == self.gold_tile else ""
            parts.append(f"{index}:{display_tile(tile)}{marker}")
        return " ".join(parts)

    def _format_score_payments(self, score: ScoreResult) -> str:
        parts = []
        for player, payment in zip(self.players, score.payments):
            sign = "+" if payment > 0 else ""
            parts.append(f"{player.name}{sign}{payment}")
        return "本局得分：" + " ".join(parts)
