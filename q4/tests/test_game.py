import logging
import random

from set_game.card import Card
from set_game.deck import Deck
from set_game.features import Color, Number, Shading, Shape
from set_game.game import play

# A set: same number, shape and shading, three different colors.
A_SET = (
    Card(Number.ONE, Shape.OVAL, Shading.SOLID, Color.RED),
    Card(Number.ONE, Shape.OVAL, Shading.SOLID, Color.GREEN),
    Card(Number.ONE, Shape.OVAL, Shading.SOLID, Color.PURPLE),
)
# Two triples that are not sets: in each, the number has exactly two equal values.
NOT_A_SET_1 = (
    Card(Number.ONE, Shape.DIAMOND, Shading.SOLID, Color.RED),
    Card(Number.ONE, Shape.DIAMOND, Shading.SOLID, Color.GREEN),
    Card(Number.TWO, Shape.DIAMOND, Shading.SOLID, Color.PURPLE),
)
NOT_A_SET_2 = (
    Card(Number.ONE, Shape.SQUIGGLE, Shading.OPEN, Color.RED),
    Card(Number.ONE, Shape.SQUIGGLE, Shading.OPEN, Color.GREEN),
    Card(Number.TWO, Shape.SQUIGGLE, Shading.OPEN, Color.PURPLE),
)


def deck_drawing(*triples):
    """A deck whose draws return these triples in this order (draw() takes from the end)."""
    return Deck(card for triple in reversed(triples) for card in reversed(triple))


def test_stops_at_the_first_set():
    result = play(deck_drawing(NOT_A_SET_1, A_SET, NOT_A_SET_2))
    assert result.found_set == A_SET
    assert result.rounds == 2
    assert result.cards_left == 3


def test_returns_no_set_when_the_deck_runs_out():
    result = play(deck_drawing(NOT_A_SET_1, NOT_A_SET_2))
    assert result.found_set is None
    assert result.rounds == 2
    assert result.cards_left == 0


def test_stops_when_fewer_than_three_cards_remain():
    leftover = NOT_A_SET_2[:2]
    result = play(Deck([*leftover, *reversed(NOT_A_SET_1)]))
    assert result.found_set is None
    assert result.rounds == 1
    assert result.cards_left == 2


def test_empty_deck_plays_no_rounds():
    result = play(Deck([]))
    assert result.found_set is None
    assert result.rounds == 0


def test_full_shuffled_game_takes_at_most_27_rounds():
    for seed in range(200):
        result = play(Deck.shuffled(random.Random(seed)))
        assert 1 <= result.rounds <= 27
        assert result.cards_left == 81 - 3 * result.rounds


def test_each_round_is_logged_as_key_value(caplog):
    with caplog.at_level(logging.INFO, logger="set_game.game"):
        play(deck_drawing(NOT_A_SET_1, A_SET))
    rounds = [r.getMessage() for r in caplog.records]
    assert rounds[0].startswith("event=round round=1 ")
    assert "is_set=false" in rounds[0]
    assert "is_set=true cards_left=0" in rounds[1]
