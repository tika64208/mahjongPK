"""Scoring helpers for supported Longyan Mahjong win types."""

from dataclasses import dataclass
from typing import Dict, List

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


def win_score_table(profile: ScoreProfile = DEFAULT_SCORE_PROFILE) -> List[WinScoreRule]:
    return sorted(profile.win_rules.values(), key=lambda rule: (rule.multiplier, rule.kind))

