"""One test per instruction in the question, checked against the observable behaviour of a game.

The set rule is checked with an independent oracle (the mod-3 rule) rather than with is_set itself.
"""

import random
from collections import Counter
from itertools import product

import pytest

from set_game.card import Card
from set_game.deck import Deck, all_cards
from set_game.features import FEATURES, Color, Number, Shading, Shape
from set_game.game import Round, play

SEEDS = range(300)


def oracle_is_set(cards: tuple[Card, ...]) -> bool:
    """Independent rule: per feature, values 0/1/2 are all same or all different iff their sum % 3 == 0."""
    return all(sum(values) % 3 == 0 for values in zip(*(c.features for c in cards)))


def play_recorded_deck(deck: Deck) -> tuple[list[Round], object]:
    """Play and keep every round. Fails fast instead of hanging if the game never uses up the deck."""
    max_rounds = len(deck) // 3
    rounds: list[Round] = []

    def record(current: Round) -> None:
        rounds.append(current)
        if len(rounds) > max_rounds:
            raise AssertionError(f"more than {max_rounds} rounds: cards are being drawn twice")

    result = play(deck, on_round=record)
    return rounds, result


def play_recorded(seed: int) -> tuple[list[Round], object]:
    return play_recorded_deck(Deck.shuffled(random.Random(seed)))


# "81 unique cards that vary in four features across three possibilities for each kind of feature"
def test_four_features_with_three_values_each():
    assert [f.__name__ for f in FEATURES] == ["Number", "Shape", "Shading", "Color"]
    assert {f: [v.name for v in f] for f in FEATURES} == {
        Number: ["ONE", "TWO", "THREE"],
        Shape: ["DIAMOND", "SQUIGGLE", "OVAL"],
        Shading: ["SOLID", "STRIPED", "OPEN"],
        Color: ["RED", "GREEN", "PURPLE"],
    }


# "Each possible combination of features appears as a card precisely once in the deck"
def test_every_combination_appears_exactly_once():
    counts = Counter(all_cards())
    assert len(counts) == 81
    assert set(counts.values()) == {1}
    assert set(counts) == {Card(*values) for values in product(*FEATURES)}


# "Draw three unique cards"
def test_each_round_draws_three_unique_cards_never_seen_before():
    for seed in SEEDS:
        rounds, _ = play_recorded(seed)
        drawn = [card for r in rounds for card in r.cards]
        assert all(len(r.cards) == 3 and len(set(r.cards)) == 3 for r in rounds)
        assert len(set(drawn)) == len(drawn)  # no card is drawn twice in a game


# "Decide whether the cards form a set" (all four rules: number, shape, shading, color)
def test_every_decision_matches_the_rules():
    for seed in SEEDS:
        rounds, _ = play_recorded(seed)
        assert all(r.is_set == oracle_is_set(r.cards) for r in rounds)


@pytest.mark.parametrize("feature", range(4))
def test_each_feature_alone_can_break_a_set(feature):
    # Start from a valid set (all different everywhere), then make exactly two values equal in one feature.
    values = [[0, 1, 2] for _ in range(4)]
    values[feature] = [0, 0, 1]
    cards = tuple(Card(*(f(values[i][k]) for i, f in enumerate(FEATURES))) for k in range(3))
    assert not oracle_is_set(cards)
    rounds, _ = play_recorded_deck(Deck(reversed(cards)))
    assert [r.is_set for r in rounds] == [False]


# "Repeat until a set is found ..."
def test_game_stops_right_after_the_first_set():
    for seed in SEEDS:
        rounds, result = play_recorded(seed)
        if result.found_set is not None:
            assert rounds[-1].is_set and rounds[-1].cards == result.found_set
            assert not any(r.is_set for r in rounds[:-1])
            assert result.cards_left == 81 - 3 * len(rounds)


# "... or the deck is empty"
def test_without_a_set_the_whole_deck_is_used():
    for seed in SEEDS:
        rounds, result = play_recorded(seed)
        if result.found_set is None:
            assert len(rounds) == 27
            assert result.cards_left == 0
            assert not any(r.is_set for r in rounds)


def test_both_endings_happen_across_seeds():
    endings = {play_recorded(seed)[1].found_set is None for seed in SEEDS}
    assert endings == {True, False}


# "Be mindful of time and space complexity": every card is drawn at most once (linear work),
# and the game itself keeps no history: rounds are only visible through the callback.
def test_game_result_does_not_store_the_drawn_cards():
    _, result = play_recorded(0)
    assert set(type(result).__slots__) == {"found_set", "rounds", "cards_left"}
