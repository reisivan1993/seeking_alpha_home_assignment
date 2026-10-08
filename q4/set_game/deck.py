"""The deck: all 81 cards, drawn from the top without replacement."""

import random
from collections.abc import Iterable
from itertools import product

from set_game.card import Card
from set_game.features import FEATURES


def all_cards() -> list[Card]:
    """Every combination of feature values, exactly once (3^4 = 81 cards)."""
    return [Card(*values) for values in product(*FEATURES)]


class Deck:
    def __init__(self, cards: Iterable[Card]) -> None:
        self._cards = list(cards)
        if len(set(self._cards)) != len(self._cards):
            raise ValueError("a deck cannot contain the same card twice")

    @classmethod
    def shuffled(cls, rng: random.Random) -> "Deck":
        cards = all_cards()
        rng.shuffle(cards)
        return cls(cards)

    def __len__(self) -> int:
        return len(self._cards)

    def draw(self, count: int) -> tuple[Card, ...]:
        """Remove and return `count` cards from the top.

        Cards are stored with the "top" at the end so removal is O(1) per card (no shifting).
        The slice is reversed so callers see them in draw order (top-of-deck first).
        """
        if count > len(self._cards):
            raise ValueError(f"cannot draw {count} cards, only {len(self._cards)} left")
        drawn = self._cards[-count:]
        del self._cards[-count:]
        return tuple(reversed(drawn))
