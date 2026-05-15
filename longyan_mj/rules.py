"""Rule configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleProfile:
    name: str
    allow_chow: bool = False
    allow_pong: bool = True
    allow_kong: bool = True
    allow_ron: bool = False
    use_flowers: bool = False
    gold_count: int = 1


LONGYAN_HALF_SELF_DRAW = RuleProfile(name="龙岩麻将半自摸 MVP", use_flowers=True)
