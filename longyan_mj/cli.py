"""Command line entrypoint."""

import argparse

from .game import MahjongGame


def main() -> int:
    parser = argparse.ArgumentParser(description="和 3 个机器人玩一局龙岩麻将 MVP。")
    parser.add_argument("--seed", type=int, default=None, help="固定随机种子，便于复现牌局。")
    args = parser.parse_args()

    game = MahjongGame(seed=args.seed)
    try:
        game.play()
    except KeyboardInterrupt:
        print("\n牌局已退出。")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

