"""Round runner for local Longyan Mahjong games."""

from collections import Counter
import random
from typing import Callable, List, Optional, Tuple

from .bot import BotContext, BotPolicy, default_bot_policies
from .evaluator import WinResult, count_gold, evaluate_qiangjin, evaluate_win, find_youjin_discard
from .rules import LONGYAN_HALF_SELF_DRAW, RuleProfile
from .scoring import (
    ScoreResult,
    combine_score_payments,
    score_kong,
    score_rob_kong,
    score_self_draw,
)
from .state import Player
from .tiles import TILE_INDEX, build_wall, display_tile, display_tiles, is_flower, sort_tiles

InputFunc = Callable[[str], str]
OutputFunc = Callable[[str], None]


class GameResult:
    def __init__(
        self,
        winner: Optional[int],
        win: Optional[WinResult],
        reason: str,
        score: Optional[ScoreResult] = None,
        discard_count: int = 0,
        draw_count: int = 0,
        pong_count: int = 0,
        kong_count: int = 0,
    ) -> None:
        self.winner = winner
        self.win = win
        self.reason = reason
        self.score = score
        self.discard_count = discard_count
        self.draw_count = draw_count
        self.pong_count = pong_count
        self.kong_count = kong_count


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
        self.discards_by_player: List[List[str]] = [[] for _ in self.players]
        self.round_payments: List[int] = [0 for _ in self.players]
        self.gold_tile: Optional[str] = None
        self.dealer = 0
        self.current = self.dealer

    def start_round(self) -> None:
        self.wall = build_wall(include_flowers=self.rules.use_flowers)
        self.random.shuffle(self.wall)
        self.gold_tile = self._pop_gold_tile()
        self.discards = []
        self.discards_by_player = [[] for _ in self.players]
        self.round_payments = [0 for _ in self.players]
        self.current = self.dealer
        for player in self.players:
            player.hand.clear()
            player.melds.clear()
            player.flowers.clear()
            player.clear_youjin()
        for _ in range(13):
            for player in self.players:
                if self._draw_hand_tile(player) is None:
                    raise RuntimeError("牌墙不足，无法完成发牌")
        if self._draw_hand_tile(self.players[self.dealer]) is None:
            raise RuntimeError("牌墙不足，无法完成庄家发牌")
        for player in self.players:
            player.sort_hand()

    def play(self, input_func: InputFunc = input, output_func: OutputFunc = print) -> GameResult:
        self.start_round()
        output_func(f"本局规则：{self.rules.name}")
        output_func(f"金牌：{display_tile(self.gold_tile)}")
        output_func("机器人能力：" + "，".join(bot.name for bot in self.bots))
        output_func("牌局开始。输入手牌编号出牌，输入 q 可退出。")

        opening_result = self._check_opening_special_win(input_func, output_func)
        if opening_result:
            return opening_result

        first_turn = True
        discard_only = False
        prepared_drawn: Optional[str] = None
        discard_count = 0
        draw_count = 0
        pong_count = 0
        kong_count = 0

        while self.wall:
            player = self.players[self.current]

            if not discard_only:
                drawn_from_kong = False
                if prepared_drawn:
                    drawn = prepared_drawn
                    prepared_drawn = None
                    drawn_from_kong = True
                elif first_turn and self.current == self.dealer:
                    first_turn = False
                    drawn = None
                else:
                    drawn = self._draw_hand_tile(player, output_func)
                    if drawn is None:
                        break
                    draw_count += 1
                    if player.is_human:
                        output_func(f"\n你摸到：{display_tile(drawn)}")
                    else:
                        output_func(f"\n{player.name} 摸牌")

                if player.youjin_level:
                    if self._apply_youjin_draw(player, drawn, output_func):
                        discard_count += 1
                        self.current = (self.current + 1) % 4
                        discard_only = False
                        continue
                    win_kind = "single_you" if player.youjin_level == 1 else "double_you"
                    win_label = "单游" if player.youjin_level == 1 else "双游"
                    win = WinResult(win_kind, win_label, 5 if player.youjin_level == 1 else 10)
                    return self._finish_win(
                        player,
                        win,
                        output_func,
                        discard_count,
                        draw_count,
                        pong_count,
                        kong_count,
                    )

                win = evaluate_win(player.hand, self.gold_tile, open_melds=len(player.melds))
                if win and drawn_from_kong:
                    win = WinResult("kong_bloom", "杠上开花", max(win.multiplier + 1, 2))
                if win and self._accept_win(player, win, input_func, output_func):
                    youjin_discard = find_youjin_discard(
                        player.hand, self.gold_tile, open_melds=len(player.melds)
                    )
                    if youjin_discard and self._accept_youjin(player, input_func, output_func):
                        player.remove_tile(youjin_discard)
                        player.youjin_level = 1
                        discard_count += 1
                        output_func(f"{player.name} 打出 {display_tile(youjin_discard)}，进入单游")
                        self.current = (self.current + 1) % 4
                        discard_only = False
                        continue
                    return self._finish_win(
                        player,
                        win,
                        output_func,
                        discard_count,
                        draw_count,
                        pong_count,
                        kong_count,
                    )

                self_kong = self._perform_self_kong(player, input_func, output_func)
                if self_kong:
                    if self_kong[3]:
                        return self_kong[3]
                    kong_count += 1
                    prepared_drawn = self_kong[2]
                    if prepared_drawn:
                        draw_count += 1
                    discard_only = False
                    continue

            discarded = self._discard(player, input_func, output_func)
            discard_count += 1
            self.discards.append(discarded)
            self.discards_by_player[self.current].append(discarded)
            output_func(f"{player.name} 打出：{display_tile(discarded)}")

            if self._apply_youjin_gold_discard(player, discarded, output_func):
                self.current = (self.current + 1) % 4
                discard_only = False
                continue

            kong_player = self._find_exposed_kong_player(discarded, input_func, output_func)
            if kong_player is not None:
                source_player = self.current
                self.discards.pop()
                self.discards_by_player[self.current].pop()
                self.players[kong_player].exposed_kong(discarded, source_player)
                kong_count += 1
                output_func(f"{self.players[kong_player].name} 明杠 {display_tile(discarded)}")
                self._apply_kong_score("exposed", kong_player, source_player, output_func)
                self.current = kong_player
                prepared_drawn = self._draw_supplement(self.players[kong_player], output_func)
                if prepared_drawn:
                    draw_count += 1
                discard_only = False
                continue

            pong_player = self._find_pong_player(discarded, input_func, output_func)
            if pong_player is not None:
                self.discards.pop()
                self.discards_by_player[self.current].pop()
                self.players[pong_player].pong(discarded, self.current)
                pong_count += 1
                output_func(f"{self.players[pong_player].name} 碰 {display_tile(discarded)}")
                self.current = pong_player
                discard_only = True
                continue

            self.current = (self.current + 1) % 4
            discard_only = False

        output_func("牌墙摸完，流局。")
        return GameResult(
            None,
            None,
            "draw",
            discard_count=discard_count,
            draw_count=draw_count,
            pong_count=pong_count,
            kong_count=kong_count,
        )

    def _check_opening_special_win(
        self, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[GameResult]:
        if not self.gold_tile:
            return None

        seat_order = [(self.dealer + offset) % 4 for offset in range(4)]
        for index in seat_order:
            player = self.players[index]
            if count_gold(player.hand, self.gold_tile) < 3:
                continue
            win = WinResult("three_gold", "三金倒", 3)
            if self._accept_win(player, win, input_func, output_func):
                self.current = index
                return self._finish_win(player, win, output_func, 0, 0, 0, 0)

        qiangjin_order = [(self.dealer + offset) % 4 for offset in range(1, 5)]
        for index in qiangjin_order:
            player = self.players[index]
            win = evaluate_qiangjin(player.hand, self.gold_tile)
            if win and self._accept_win(player, win, input_func, output_func):
                self.current = index
                return self._finish_win(player, win, output_func, 0, 0, 0, 0)

        return None

    def _pop_gold_tile(self) -> str:
        for index in range(len(self.wall) - 1, -1, -1):
            tile = self.wall[index]
            if not is_flower(tile):
                return self.wall.pop(index)
        raise RuntimeError("牌墙中没有可作为金牌的普通牌")

    def _draw_hand_tile(
        self, player: Player, output_func: Optional[OutputFunc] = None
    ) -> Optional[str]:
        while self.wall:
            tile = self.wall.pop()
            if is_flower(tile):
                player.flowers.append(tile)
                if output_func:
                    output_func(f"{player.name} 补花：{display_tile(tile)}")
                continue
            player.hand.append(tile)
            player.sort_hand()
            return tile
        return None

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

    def _accept_youjin(
        self, player: Player, input_func: InputFunc, output_func: OutputFunc
    ) -> bool:
        if not player.is_human:
            return True
        output_func(f"你的手牌：{self._numbered_hand(player)}")
        while True:
            answer = input_func("可进入单游，是否游金？[y/n] ").strip().lower()
            if answer in ("y", "yes", "you", "游", "游金"):
                return True
            if answer in ("n", "no", ""):
                return False
            output_func("请输入 y 或 n。")

    def _finish_win(
        self,
        player: Player,
        win: WinResult,
        output_func: OutputFunc,
        discard_count: int,
        draw_count: int,
        pong_count: int,
        kong_count: int,
        score: Optional[ScoreResult] = None,
        reason: str = "win",
    ) -> GameResult:
        winner_index = self.players.index(player)
        if score is None:
            score = score_self_draw(winner_index, self.dealer, win)
        if any(self.round_payments):
            score = combine_score_payments(score, self.round_payments)
        player.clear_youjin()
        output_func(
            f"{player.name} 胡牌：{score.win_label}，"
            f"{score.multiplier} 倍，得分 +{score.total_gain}，"
            f"手牌 {display_tiles(player.hand)}"
        )
        output_func(self._format_score_payments(score))
        return GameResult(
            winner_index,
            win,
            reason,
            score=score,
            discard_count=discard_count,
            draw_count=draw_count,
            pong_count=pong_count,
            kong_count=kong_count,
        )

    def _discard(self, player: Player, input_func: InputFunc, output_func: OutputFunc) -> str:
        if player.is_human:
            return self._human_discard(player, input_func, output_func)
        tile = self._bot_for_player(self.current).choose_discard(
            player.hand,
            self.gold_tile,
            open_melds=len(player.melds),
            context=self._bot_context(self.current),
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

    def _apply_youjin_gold_discard(
        self, player: Player, discarded: str, output_func: OutputFunc
    ) -> bool:
        if player.youjin_level == 1 and discarded == self.gold_tile:
            player.youjin_level = 2
            output_func(f"{player.name} 进入双游")
            return True
        return False

    def _apply_youjin_draw(
        self, player: Player, drawn: Optional[str], output_func: OutputFunc
    ) -> bool:
        if player.youjin_level == 1 and drawn == self.gold_tile:
            player.remove_tile(self.gold_tile)
            player.youjin_level = 2
            output_func(f"{player.name} 摸到金牌，进入双游")
            return True
        return False

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
                player.hand,
                discarded,
                self.gold_tile,
                open_melds=len(player.melds),
                context=self._bot_context(index),
            ):
                return index
        return None

    def _find_exposed_kong_player(
        self, discarded: str, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[int]:
        if not self.rules.allow_kong:
            return None
        for offset in range(1, 4):
            index = (self.current + offset) % 4
            player = self.players[index]
            if not player.can_exposed_kong(discarded, self.gold_tile):
                continue
            if player.is_human:
                output_func(f"你的手牌：{self._numbered_hand(player)}")
                answer = input_func(f"是否明杠 {display_tile(discarded)}？[y/n] ").strip().lower()
                if answer in ("y", "yes", "g", "gang", "杠"):
                    return index
            elif self._bot_for_player(index).wants_exposed_kong(
                player.hand,
                discarded,
                self.gold_tile,
                open_melds=len(player.melds),
                context=self._bot_context(index),
            ):
                return index
        return None

    def _perform_self_kong(
        self, player: Player, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[Tuple[str, str, Optional[str], Optional[GameResult]]]:
        if not self.rules.allow_kong:
            return None
        choice = self._choose_self_kong(player, input_func, output_func)
        if choice is None:
            return None
        kind, tile = choice
        if kind == "concealed":
            player.concealed_kong(tile, self.current)
            output_func(f"{player.name} 暗杠 {display_tile(tile)}")
            self._apply_kong_score("concealed", self.current, None, output_func)
        else:
            robbed_result = self._check_rob_kong(tile, input_func, output_func)
            if robbed_result is not None:
                return kind, tile, None, robbed_result
            player.added_kong(tile)
            output_func(f"{player.name} 补杠 {display_tile(tile)}")
            self._apply_kong_score("added", self.current, None, output_func)
        return kind, tile, self._draw_supplement(player, output_func), None

    def _check_rob_kong(
        self, tile: str, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[GameResult]:
        if not self.rules.allow_rob_kong:
            return None
        robbed_player = self.current
        for offset in range(1, 4):
            index = (robbed_player + offset) % 4
            player = self.players[index]
            if player.youjin_level:
                continue
            win = evaluate_win(player.hand + [tile], self.gold_tile, open_melds=len(player.melds))
            if not win:
                continue
            if player.is_human:
                output_func(f"你的手牌：{self._numbered_hand(player)}")
                answer = input_func(f"可抢杠胡 {display_tile(tile)}，是否胡？[y/n] ").strip().lower()
                if answer not in ("y", "yes", "h", "hu", "胡"):
                    continue
            self.current = index
            rob_win = WinResult("rob_kong", "抢杠胡", win.multiplier)
            score = score_rob_kong(index, robbed_player, self.dealer, win)
            output_func(f"{player.name} 抢杠胡 {display_tile(tile)}")
            return self._finish_win(
                player,
                rob_win,
                output_func,
                discard_count=0,
                draw_count=0,
                pong_count=0,
                kong_count=0,
                score=score,
                reason="rob_kong",
            )
        return None

    def _apply_kong_score(
        self,
        kind: str,
        kong_player: int,
        source_player: Optional[int],
        output_func: OutputFunc,
    ) -> ScoreResult:
        score = score_kong(kind, kong_player, self.dealer, source_player)
        self.round_payments = [
            payment + score.payments[index] for index, payment in enumerate(self.round_payments)
        ]
        output_func(f"{score.win_label}得分：" + self._format_score_payments(score))
        return score

    def _choose_self_kong(
        self, player: Player, input_func: InputFunc, output_func: OutputFunc
    ) -> Optional[Tuple[str, str]]:
        options = self._available_self_kongs(player)
        if not options:
            return None

        if player.is_human:
            labels = [
                f"{index}:{'暗杠' if kind == 'concealed' else '补杠'} {display_tile(tile)}"
                for index, (kind, tile) in enumerate(options, start=1)
            ]
            output_func("可杠：" + " ".join(labels))
            answer = input_func("输入编号杠，直接回车跳过：").strip().lower()
            if not answer:
                return None
            if answer.isdigit():
                index = int(answer) - 1
                if 0 <= index < len(options):
                    return options[index]
            output_func("杠牌编号无效，已跳过。")
            return None

        bot = self._bot_for_player(self.current)
        for kind, tile in options:
            if kind == "concealed" and bot.wants_concealed_kong(
                player.hand,
                tile,
                self.gold_tile,
                open_melds=len(player.melds),
                context=self._bot_context(self.current),
            ):
                return kind, tile
            if kind == "added" and bot.wants_added_kong(
                player.hand,
                tile,
                self.gold_tile,
                open_melds=len(player.melds),
                context=self._bot_context(self.current),
            ):
                return kind, tile
        return None

    def _available_self_kongs(self, player: Player) -> List[Tuple[str, str]]:
        if not self.gold_tile:
            return []
        options: List[Tuple[str, str]] = []
        counts = Counter(player.hand)
        for tile in sorted(counts, key=lambda item: TILE_INDEX[item]):
            if player.can_concealed_kong(tile, self.gold_tile):
                options.append(("concealed", tile))
        for meld in player.melds:
            tile = meld.tiles[0]
            if player.can_added_kong(tile, self.gold_tile):
                options.append(("added", tile))
        return options

    def _draw_supplement(self, player: Player, output_func: OutputFunc) -> Optional[str]:
        if not self.wall:
            output_func("牌墙已空，无法补牌。")
            return None
        drawn = self._draw_hand_tile(player, output_func)
        if drawn is None:
            output_func("牌墙已空，无法补牌。")
            return None
        if player.is_human:
            output_func(f"杠后补到：{display_tile(drawn)}")
        else:
            output_func(f"{player.name} 杠后补牌")
        return drawn

    def _bot_for_player(self, player_index: int) -> BotPolicy:
        bot_index = player_index - 1 if player_index > self.human_index else player_index
        return self.bots[bot_index % len(self.bots)]

    def _bot_context(self, player_index: int) -> BotContext:
        visible_counts = Counter()
        if self.gold_tile:
            visible_counts[self.gold_tile] += 1
        for tile in self.discards:
            visible_counts[tile] += 1
        melds_by_player = []
        for player in self.players:
            player_melds = []
            for meld in player.melds:
                visible_counts.update(meld.tiles)
                player_melds.append(tuple(meld.tiles))
            melds_by_player.append(tuple(player_melds))
        return BotContext(
            current_player=player_index,
            dealer=self.dealer,
            wall_remaining=len(self.wall),
            visible_counts=visible_counts,
            discards_by_player=tuple(tuple(tiles) for tiles in self.discards_by_player),
            melds_by_player=tuple(melds_by_player),
        )

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
