import random

import pytest

from set_game.card import Card
from set_game.deck import Deck, all_cards
from set_game.features import Color, Number, Shading, Shape


def test_all_cards_has_81_unique_cards():
    cards = all_cards()
    assert len(cards) == 81
    assert len(set(cards)) == 81


def test_example_card_from_the_question_appears_once():
    three_striped_green_diamonds = Card(Number.THREE, Shape.DIAMOND, Shading.STRIPED, Color.GREEN)
    assert all_cards().count(three_striped_green_diamonds) == 1


def test_draw_removes_cards_from_the_deck():
    deck = Deck.shuffled(random.Random(1))
    drawn = deck.draw(3)
    assert len(drawn) == 3
    assert len(deck) == 78


def test_drawing_the_whole_deck_never_repeats_a_card():
    deck = Deck.shuffled(random.Random(1))
    drawn = [card for _ in range(27) for card in deck.draw(3)]
    assert len(set(drawn)) == 81
    assert len(deck) == 0


def test_same_seed_gives_the_same_order():
    assert Deck.shuffled(random.Random(7)).draw(81) == Deck.shuffled(random.Random(7)).draw(81)


def test_draw_takes_cards_from_the_top_in_order():
    cards = all_cards()[:4]
    deck = Deck(cards)
    assert deck.draw(2) == (cards[3], cards[2])


def test_cannot_draw_more_cards_than_are_left():
    deck = Deck(all_cards()[:2])
    with pytest.raises(ValueError, match="only 2 left"):
        deck.draw(3)


def test_deck_rejects_duplicate_cards():
    card = all_cards()[0]
    with pytest.raises(ValueError, match="same card twice"):
        Deck([card, card])
