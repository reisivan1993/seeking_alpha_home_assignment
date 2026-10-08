"""The game loop: draw three cards, check them, repeat until a set or an empty deck."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from set_game.card import Card
from set_game.deck import Deck
from set_game.rules import is_set

CARDS_PER_DRAW = 3

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Round:
    number: int
    cards: tuple[Card, ...]
    is_set: bool
    cards_left: int


@dataclass(frozen=True, slots=True)
class GameResult:
    found_set: tuple[Card, ...] | None
    rounds: int
    cards_left: int


def play(deck: Deck, on_round: Callable[[Round], None] | None = None) -> GameResult:
    """Draw three cards per round and stop at the first set, or when fewer than three cards remain.

    Each round is O(1), so a full 81-card deck takes at most 27 rounds. Drawn cards that are not
    a set are discarded, so nothing besides the deck is kept in memory. `on_round` lets a caller
    (such as the web UI) see every round without the game storing them.
    """
    rounds = 0
    while len(deck) >= CARDS_PER_DRAW:
        rounds += 1
        cards = deck.draw(CARDS_PER_DRAW)
        current = Round(number=rounds, cards=cards, is_set=is_set(*cards), cards_left=len(deck))
        logger.info(
            "event=round round=%d cards=%s is_set=%s cards_left=%d",
            current.number, ",".join(map(str, cards)), str(current.is_set).lower(), current.cards_left,
        )
        if on_round is not None:
            on_round(current)
        if current.is_set:
            return GameResult(found_set=cards, rounds=rounds, cards_left=len(deck))
    return GameResult(found_set=None, rounds=rounds, cards_left=len(deck))
