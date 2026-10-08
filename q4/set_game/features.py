"""The four card features. Each has exactly three values, numbered 0, 1, 2."""

from enum import IntEnum


class Number(IntEnum):
    ONE = 0
    TWO = 1
    THREE = 2


class Shape(IntEnum):
    DIAMOND = 0
    SQUIGGLE = 1
    OVAL = 2


class Shading(IntEnum):
    SOLID = 0
    STRIPED = 1
    OPEN = 2


class Color(IntEnum):
    RED = 0
    GREEN = 1
    PURPLE = 2


FEATURES: tuple[type[IntEnum], ...] = (Number, Shape, Shading, Color)
