from itertools import combinations

import pytest

from set_game.card import Card
from set_game.deck import all_cards
from set_game.features import Color, Number, Shading, Shape
from set_game.rules import is_set


def card(number, shape, shading, color):
    return Card(Number[number], Shape[shape], Shading[shading], Color[color])


def test_three_same_features_and_one_all_different_is_a_set():
    assert is_set(
        card("ONE", "OVAL", "SOLID", "RED"),
        card("ONE", "OVAL", "SOLID", "GREEN"),
        card("ONE", "OVAL", "SOLID", "PURPLE"),
    )


def test_all_features_all_different_is_a_set():
    assert is_set(
        card("ONE", "DIAMOND", "SOLID", "RED"),
        card("TWO", "SQUIGGLE", "STRIPED", "GREEN"),
        card("THREE", "OVAL", "OPEN", "PURPLE"),
    )


def test_two_of_one_value_in_a_single_feature_is_not_a_set():
    # colors red, red, green: exactly two the same, everything else is valid
    assert not is_set(
        card("ONE", "DIAMOND", "SOLID", "RED"),
        card("TWO", "SQUIGGLE", "STRIPED", "RED"),
        card("THREE", "OVAL", "OPEN", "GREEN"),
    )


def test_card_order_does_not_matter():
    a, b, c = (
        card("ONE", "DIAMOND", "SOLID", "RED"),
        card("TWO", "DIAMOND", "STRIPED", "RED"),
        card("THREE", "DIAMOND", "OPEN", "RED"),
    )
    assert is_set(a, b, c) and is_set(c, a, b) and is_set(b, c, a)


def test_repeated_card_is_rejected():
    a = card("ONE", "DIAMOND", "SOLID", "RED")
    b = card("TWO", "DIAMOND", "SOLID", "RED")
    with pytest.raises(ValueError, match="three different cards"):
        is_set(a, a, b)


def test_full_deck_contains_exactly_1080_sets():
    # Any two cards are completed by exactly one third card, so there are 81*80/6 = 1080 sets.
    assert sum(is_set(*triple) for triple in combinations(all_cards(), 3)) == 1080
