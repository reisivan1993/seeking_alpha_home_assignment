"""A single card: one value for each of the four features."""

from dataclasses import dataclass

from set_game.features import Color, Number, Shading, Shape


@dataclass(frozen=True, slots=True)
class Card:
    number: Number
    shape: Shape
    shading: Shading
    color: Color

    @property
    def features(self) -> tuple[Number, Shape, Shading, Color]:
        return (self.number, self.shape, self.shading, self.color)

    def __str__(self) -> str:
        return "-".join(feature.name.lower() for feature in self.features)
