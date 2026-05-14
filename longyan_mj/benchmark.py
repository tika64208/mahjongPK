"""Benchmark purchasable bot abilities."""

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple

from .bot import (
    ABILITY_BASIC_TILE_EFFICIENCY,
    ABILITY_DANGER_REFINED,
    ABILITY_DEFENSE,
    ABILITY_EFFECTIVE_DRAWS,
    ABILITY_EXPLANATION,
    ABILITY_GOLD_STRATEGY,
    ABILITY_HAND_VALUE,
    ABILITY_KONG_EV,
    ABILITY_MONTE_CARLO,
    ABILITY_OPPONENT_TENPAI,
    ABILITY_PONG_EV,
    ABILITY_REMAINING_TILES,
    ABILITY_SHANTEN,
    ABILITY_STYLE_CONTROL,
    ABILITY_YOUJIN_STRATEGY,
    AbilityConfig,
    build_bot_from_abilities,
)
from .game import MahjongGame


EXPERIMENT_SEAT = 3
BENCHMARK_PLAYER_NAMES = ["玩家1", "玩家2", "玩家3", "玩家4"]

ALL_ABILITIES = [
    ABILITY_SHANTEN,
    ABILITY_EFFECTIVE_DRAWS,
    ABILITY_REMAINING_TILES,
    ABILITY_HAND_VALUE,
    ABILITY_PONG_EV,
    ABILITY_DEFENSE,
    ABILITY_GOLD_STRATEGY,
    ABILITY_STYLE_CONTROL,
    ABILITY_OPPONENT_TENPAI,
    ABILITY_DANGER_REFINED,
    ABILITY_KONG_EV,
    ABILITY_YOUJIN_STRATEGY,
    ABILITY_MONTE_CARLO,
    ABILITY_EXPLANATION,
]

ABILITY_PACKS: Dict[str, List[str]] = {
    "baseline": [ABILITY_BASIC_TILE_EFFICIENCY],
    "tile_efficiency": [ABILITY_SHANTEN, ABILITY_EFFECTIVE_DRAWS],
    "reading": [ABILITY_SHANTEN, ABILITY_EFFECTIVE_DRAWS, ABILITY_REMAINING_TILES],
    "value_routes": [ABILITY_HAND_VALUE, ABILITY_GOLD_STRATEGY, ABILITY_YOUJIN_STRATEGY],
    "pong_judgement": [ABILITY_SHANTEN, ABILITY_PONG_EV],
    "defense": [ABILITY_DEFENSE, ABILITY_OPPONENT_TENPAI, ABILITY_DANGER_REFINED],
    "simulation": [
        ABILITY_SHANTEN,
        ABILITY_EFFECTIVE_DRAWS,
        ABILITY_REMAINING_TILES,
        ABILITY_MONTE_CARLO,
    ],
    "training_hint": [
        ABILITY_EXPLANATION,
        ABILITY_SHANTEN,
        ABILITY_EFFECTIVE_DRAWS,
        ABILITY_REMAINING_TILES,
    ],
    "expert": ALL_ABILITIES,
}


@dataclass
class ExperimentResult:
    name: str
    abilities: List[str]
    games: int
    wins: int
    draws: int
    total_score: int
    avg_score: float
    win_rate: float
    non_draw_win_rate: float
    avg_discards: float
    elapsed_seconds: float
    win_kinds: Dict[str, int]
    ability_score: int = 0
    win_rate_delta: float = 0.0
    avg_score_delta: float = 0.0


def ability_config(ability_ids: Sequence[str]) -> AbilityConfig:
    ids = [ABILITY_BASIC_TILE_EFFICIENCY]
    ids.extend(ability_id for ability_id in ability_ids if ability_id != ABILITY_BASIC_TILE_EFFICIENCY)
    return AbilityConfig.from_ids(ids)


def baseline_abilities_for_level(level: str) -> List[str]:
    if level == "a":
        return []
    if level == "b":
        return [ABILITY_SHANTEN]
    if level == "c":
        return ALL_ABILITIES
    raise ValueError(f"Unknown baseline level: {level}")


def run_experiment(
    name: str,
    ability_ids: Sequence[str],
    games: int,
    seed_start: int,
    baseline_level: str = "a",
) -> ExperimentResult:
    abilities = ability_config(ability_ids)
    experiment_bot = build_bot_from_abilities(name, abilities)
    baseline_bot = build_bot_from_abilities(
        f"baseline-{baseline_level}",
        ability_config(baseline_abilities_for_level(baseline_level)),
    )
    bot_policies = [baseline_bot, baseline_bot, experiment_bot]

    wins = 0
    draws = 0
    total_score = 0
    discards: List[int] = []
    win_kinds: Counter = Counter()
    started = time.perf_counter()

    for seed in range(seed_start, seed_start + games):
        game = MahjongGame(seed=seed, bot_policies=bot_policies)
        for player, player_name in zip(game.players, BENCHMARK_PLAYER_NAMES):
            player.name = player_name
        for player in game.players:
            player.is_human = False
        result = game.play(input_func=lambda prompt: "", output_func=lambda msg: None)
        discards.append(result.discard_count)

        if result.winner is None:
            draws += 1
        else:
            if result.winner == EXPERIMENT_SEAT:
                wins += 1
            if result.score:
                total_score += result.score.payments[EXPERIMENT_SEAT]
                win_kinds[result.score.win_label] += 1

    elapsed = time.perf_counter() - started
    non_draw = games - draws
    return ExperimentResult(
        name=name,
        abilities=ability_config(ability_ids).enabled_ids(),
        games=games,
        wins=wins,
        draws=draws,
        total_score=total_score,
        avg_score=total_score / games,
        win_rate=wins / games,
        non_draw_win_rate=wins / non_draw if non_draw else 0.0,
        avg_discards=mean(discards) if discards else 0.0,
        elapsed_seconds=elapsed,
        win_kinds=dict(win_kinds),
    )


def run_experiment_shard(
    name: str,
    ability_ids: Sequence[str],
    seed_start: int,
    games: int,
    baseline_level: str = "a",
) -> ExperimentResult:
    return run_experiment(name, ability_ids, games, seed_start, baseline_level)


def merge_results(name: str, ability_ids: Sequence[str], shards: Sequence[ExperimentResult]) -> ExperimentResult:
    games = sum(shard.games for shard in shards)
    wins = sum(shard.wins for shard in shards)
    draws = sum(shard.draws for shard in shards)
    total_score = sum(shard.total_score for shard in shards)
    elapsed = sum(shard.elapsed_seconds for shard in shards)
    win_kinds: Counter = Counter()
    weighted_discards = 0.0
    for shard in shards:
        win_kinds.update(shard.win_kinds)
        weighted_discards += shard.avg_discards * shard.games
    non_draw = games - draws
    return ExperimentResult(
        name=name,
        abilities=ability_config(ability_ids).enabled_ids(),
        games=games,
        wins=wins,
        draws=draws,
        total_score=total_score,
        avg_score=total_score / games if games else 0.0,
        win_rate=wins / games if games else 0.0,
        non_draw_win_rate=wins / non_draw if non_draw else 0.0,
        avg_discards=weighted_discards / games if games else 0.0,
        elapsed_seconds=elapsed,
        win_kinds=dict(win_kinds),
    )


def score_result(result: ExperimentResult, baseline: ExperimentResult) -> ExperimentResult:
    result.win_rate_delta = result.win_rate - baseline.win_rate
    result.avg_score_delta = result.avg_score - baseline.avg_score
    result.ability_score = ability_score(result, baseline)
    return result


def ability_score(result: ExperimentResult, baseline: ExperimentResult) -> int:
    win_delta = result.win_rate - baseline.win_rate
    score_delta = result.avg_score - baseline.avg_score
    elapsed_ratio = result.elapsed_seconds / baseline.elapsed_seconds if baseline.elapsed_seconds else 1.0

    points = 0
    if win_delta > 0.10:
        points += 65
    elif win_delta > 0.06:
        points += 55
    elif win_delta > 0.03:
        points += 40
    elif win_delta > 0.01:
        points += 25
    elif win_delta > 0:
        points += 10

    if score_delta > 0.6:
        points += 20
    elif score_delta > 0.3:
        points += 15
    elif score_delta > 0.1:
        points += 10
    elif score_delta > 0:
        points += 5

    if result.draws <= baseline.draws:
        points += 3

    if elapsed_ratio > 6:
        points -= 10
    elif elapsed_ratio > 3:
        points -= 6
    elif elapsed_ratio > 1.5:
        points -= 3

    return max(0, min(100, points))


def experiments_for_mode(mode: str) -> Dict[str, List[str]]:
    if mode == "single":
        return {ability: [ability] for ability in ALL_ABILITIES}
    if mode == "packs":
        return {name: abilities for name, abilities in ABILITY_PACKS.items() if name != "baseline"}
    if mode == "ablation":
        return {
            f"expert_without_{ability}": [
                item for item in ALL_ABILITIES if item != ability
            ]
            for ability in ALL_ABILITIES
        }
    raise ValueError(f"Unknown benchmark mode: {mode}")


def shard_ranges(games: int, seed_start: int, shard_size: int) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    remaining = games
    current_seed = seed_start
    while remaining > 0:
        count = min(shard_size, remaining)
        ranges.append((current_seed, count))
        current_seed += count
        remaining -= count
    return ranges


def run_suite(
    mode: str,
    games: int,
    seed_start: int,
    workers: int = 1,
    shard_size: int = 100,
    only: str = "",
    baseline_level: str = "a",
) -> Dict[str, object]:
    baseline_ability_ids = baseline_abilities_for_level(baseline_level)
    baseline = run_experiment("baseline", baseline_ability_ids, games, seed_start, baseline_level)
    experiment_specs = experiments_for_mode(mode)
    if only:
        if only not in experiment_specs:
            raise ValueError(f"Unknown experiment for mode {mode}: {only}")
        experiment_specs = {only: experiment_specs[only]}
    results = [baseline]

    if workers <= 1:
        for name, abilities in experiment_specs.items():
            results.append(
                score_result(
                    run_experiment(name, abilities, games, seed_start, baseline_level),
                    baseline,
                )
            )
    else:
        executor = ProcessPoolExecutor(max_workers=workers)
        try:
            futures = {}
            for name, abilities in experiment_specs.items():
                for shard_seed, shard_games in shard_ranges(games, seed_start, shard_size):
                    future = executor.submit(
                        run_experiment_shard,
                        name,
                        abilities,
                        shard_seed,
                        shard_games,
                        baseline_level,
                    )
                    futures[future] = (name, abilities)
            completed: Dict[str, List[ExperimentResult]] = {
                name: [] for name in experiment_specs
            }
            for future in as_completed(futures):
                name, _abilities = futures[future]
                completed[name].append(future.result())
                shard_count = len(completed[name])
                total_shards = len(shard_ranges(games, seed_start, shard_size))
                print(f"completed {name} shard {shard_count}/{total_shards}", flush=True)
            for name in experiment_specs:
                merged = merge_results(name, experiment_specs[name], completed[name])
                results.append(score_result(merged, baseline))
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    return {
        "mode": mode,
        "games": games,
        "seed_start": seed_start,
        "workers": workers,
        "shard_size": shard_size,
        "baseline_level": baseline_level,
        "baseline": to_dict(baseline),
        "experiments": [to_dict(result) for result in results[1:]],
    }


def to_dict(result: ExperimentResult) -> Dict[str, object]:
    return {
        "name": result.name,
        "abilities": result.abilities,
        "games": result.games,
        "wins": result.wins,
        "draws": result.draws,
        "total_score": result.total_score,
        "avg_score": round(result.avg_score, 4),
        "win_rate": round(result.win_rate, 4),
        "non_draw_win_rate": round(result.non_draw_win_rate, 4),
        "avg_discards": round(result.avg_discards, 2),
        "elapsed_seconds": round(result.elapsed_seconds, 3),
        "win_kinds": result.win_kinds,
        "win_rate_delta": round(result.win_rate_delta, 4),
        "avg_score_delta": round(result.avg_score_delta, 4),
        "ability_score": result.ability_score,
    }


def render_markdown(report: Dict[str, object]) -> str:
    baseline = report["baseline"]
    rows = report["experiments"]
    lines = [
        "# 机器人能力 Benchmark 报告",
        "",
        f"- 模式：`{report['mode']}`",
        f"- 每组局数：{report['games']}",
        f"- 起始 seed：{report['seed_start']}",
        f"- 并行 workers：{report.get('workers', 1)}",
        f"- 分片大小：{report.get('shard_size', report['games'])}",
        f"- 对手基准等级：{report.get('baseline_level', 'a').upper()}",
        "",
        "## Baseline",
        "",
        "| 组别 | 胜率 | 平均分 | 流局 | 平均出牌 | 耗时秒 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {baseline['name']} | {baseline['win_rate']:.2%} | "
            f"{baseline['avg_score']:.2f} | {baseline['draws']} | "
            f"{baseline['avg_discards']:.2f} | {baseline['elapsed_seconds']:.3f} |"
        ),
        "",
        "## Experiments",
        "",
        "| 实验组 | 胜率 | 胜率提升 | 平均分 | 得分提升 | 流局 | 平均出牌 | 能力评分 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['win_rate']:.2%} | {row['win_rate_delta']:.2%} | "
            f"{row['avg_score']:.2f} | {row['avg_score_delta']:.2f} | "
            f"{row['draws']} | {row['avg_discards']:.2f} | {row['ability_score']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(report: Dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"ability-benchmark-{report['mode']}-{report['games']}"
    (output_dir / f"{stem}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / f"{stem}.md").write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Longyan Mahjong bot abilities.")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--mode", choices=["single", "packs", "ablation"], default="packs")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--output-dir", default="docs/benchmark-results")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes for experiments. Baseline runs once first.",
    )
    parser.add_argument("--shard-size", type=int, default=100)
    parser.add_argument("--only", default="", help="Run only one experiment name from the selected mode.")
    parser.add_argument("--baseline-level", choices=["a", "b", "c"], default="a")
    args = parser.parse_args()

    max_workers = max(1, min(args.workers, os.cpu_count() or 1))
    report = run_suite(
        args.mode,
        args.games,
        args.seed_start,
        max_workers,
        max(1, args.shard_size),
        args.only,
        args.baseline_level,
    )
    write_outputs(report, Path(args.output_dir))
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
