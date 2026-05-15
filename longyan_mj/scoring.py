"""Scoring helpers for supported Longyan Mahjong win types."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .evaluator import WinResult


@dataclass(frozen=True)
class WinScoreRule:
    kind: str
    label: str
    multiplier: int
    description: str


@dataclass(frozen=True)
class ScoreProfile:
    base_score: int = 1
    dealer_multiplier: int = 2
    win_rules: Dict[str, WinScoreRule] = None

    def __post_init__(self) -> None:
        if self.win_rules is None:
            object.__setattr__(self, "win_rules", DEFAULT_WIN_RULES)


@dataclass(frozen=True)
class ScoreResult:
    winner: int
    win_label: str
    multiplier: int
    payments: List[int]
    total_gain: int


DEFAULT_WIN_RULES: Dict[str, WinScoreRule] = {
    "standard": WinScoreRule("standard", "普通自摸", 1, "普通 4 副牌加 1 对将自摸。"),
    "seven_pairs": WinScoreRule("seven_pairs", "七对自摸", 3, "七个对子自摸。"),
    "three_gold": WinScoreRule("three_gold", "三金倒", 3, "手中有 3 张金牌直接胡。"),
    "thirteen_orphans": WinScoreRule(
        "thirteen_orphans", "十三幺", 20, "按三游等级参考结算。"
    ),
    "qiang_jin": WinScoreRule("qiang_jin", "抢金", 4, "翻金后起手听牌抢金胡。"),
    "kong_bloom": WinScoreRule("kong_bloom", "杠上开花", 2, "杠后补牌自摸。"),
    "single_you": WinScoreRule("single_you", "单游", 5, "游金胡。"),
    "double_you": WinScoreRule("double_you", "双游", 10, "双游胡。"),
    "triple_you": WinScoreRule("triple_you", "三游", 20, "三游胡。"),
    "seven_pairs_single_you": WinScoreRule("seven_pairs_single_you", "七对单游", 6, "七对游金。"),
    "seven_pairs_double_you": WinScoreRule("seven_pairs_double_you", "七对双游", 12, "七对双游。"),
    "seven_pairs_triple_you": WinScoreRule("seven_pairs_triple_you", "七对三游", 24, "七对三游。"),
}


DEFAULT_SCORE_PROFILE = ScoreProfile()


def score_self_draw(
    winner: int,
    dealer: int,
    win: WinResult,
    profile: ScoreProfile = DEFAULT_SCORE_PROFILE,
    player_count: int = 4,
) -> ScoreResult:
    """Score a self-draw win.

    Every loser pays base_score * win multiplier. Dealer payments are doubled:
    the dealer pays double when losing, and every loser pays double when the
    dealer wins.
    """
    rule = profile.win_rules.get(win.kind)
    multiplier = rule.multiplier if rule else win.multiplier
    payments = [0] * player_count
    for player_index in range(player_count):
        if player_index == winner:
            continue
        amount = profile.base_score * multiplier
        if winner == dealer or player_index == dealer:
            amount *= profile.dealer_multiplier
        payments[player_index] = -amount
        payments[winner] += amount
    return ScoreResult(
        winner=winner,
        win_label=rule.label if rule else win.label,
        multiplier=multiplier,
        payments=payments,
        total_gain=payments[winner],
    )


def score_rob_kong(
    winner: int,
    robbed_player: int,
    dealer: int,
    win: WinResult,
    profile: ScoreProfile = DEFAULT_SCORE_PROFILE,
    player_count: int = 4,
) -> ScoreResult:
    """Score a rob-kong win where the robbed player pays the full self-draw value."""
    base_score = score_self_draw(winner, dealer, win, profile, player_count)
    payments = [0] * player_count
    payments[winner] = base_score.total_gain
    payments[robbed_player] = -base_score.total_gain
    return ScoreResult(
        winner=winner,
        win_label="抢杠胡",
        multiplier=base_score.multiplier,
        payments=payments,
        total_gain=payments[winner],
    )


def score_kong(
    kong_kind: str,
    kong_player: int,
    dealer: int,
    source_player: Optional[int] = None,
    profile: ScoreProfile = DEFAULT_SCORE_PROFILE,
    player_count: int = 4,
) -> ScoreResult:
    """Score a kong.

    concealed kongs are worth two base units; exposed and added kongs are worth
    one. If source_player is provided, that player pays the whole kong value.
    """
    multiplier = 2 if kong_kind == "concealed" else 1
    payments = [0] * player_count
    for player_index in range(player_count):
        if player_index == kong_player:
            continue
        amount = profile.base_score * multiplier
        if kong_player == dealer or player_index == dealer:
            amount *= profile.dealer_multiplier
        payments[player_index] = -amount
        payments[kong_player] += amount

    if source_player is not None:
        total = payments[kong_player]
        payments = [0] * player_count
        payments[kong_player] = total
        payments[source_player] = -total

    labels = {
        "exposed": "明杠",
        "concealed": "暗杠",
        "added": "补杠",
    }
    return ScoreResult(
        winner=kong_player,
        win_label=labels.get(kong_kind, "杠"),
        multiplier=multiplier,
        payments=payments,
        total_gain=payments[kong_player],
    )


def combine_score_payments(score: ScoreResult, extra_payments: List[int]) -> ScoreResult:
    payments = [
        payment + (extra_payments[index] if index < len(extra_payments) else 0)
        for index, payment in enumerate(score.payments)
    ]
    total_gain = payments[score.winner] if 0 <= score.winner < len(payments) else 0
    return ScoreResult(
        winner=score.winner,
        win_label=score.win_label,
        multiplier=score.multiplier,
        payments=payments,
        total_gain=total_gain,
    )


def win_score_table(profile: ScoreProfile = DEFAULT_SCORE_PROFILE) -> List[WinScoreRule]:
    return sorted(profile.win_rules.values(), key=lambda rule: (rule.multiplier, rule.kind))
