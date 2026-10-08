"""Run one game: python -m set_game [--seed N]"""

import argparse
import logging
import random

from set_game.deck import Deck
from set_game.game import play

logger = logging.getLogger("set_game")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw three cards at a time until a set is found.")
    parser.add_argument("--seed", type=int, default=None, help="shuffle seed, to replay a game")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="level=%(levelname)s %(message)s")
    result = play(Deck.shuffled(random.Random(args.seed)))
    cards = ",".join(map(str, result.found_set)) if result.found_set else "none"
    logger.info(
        "event=game_over seed=%s set_found=%s cards=%s rounds=%d cards_left=%d",
        args.seed, str(result.found_set is not None).lower(), cards, result.rounds, result.cards_left,
    )


if __name__ == "__main__":
    main()
