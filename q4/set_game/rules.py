"""The matching rule: when do three cards form a set."""

from set_game.card import Card


def is_set(first: Card, second: Card, third: Card) -> bool:
    """True when, for every feature, the three values are all the same or all different.

    "All the same" and "all different" are exactly the cases where the three values do not
    contain precisely two distinct values. O(number of features) time, O(1) space.
    """
    if len({first, second, third}) != 3:
        raise ValueError("a set needs three different cards")
    return all(
        len({a, b, c}) != 2
        for a, b, c in zip(first.features, second.features, third.features, strict=True)
    )
