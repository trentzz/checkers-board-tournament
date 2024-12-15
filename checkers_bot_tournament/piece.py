from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class Colour(Enum):
    WHITE = auto()
    BLACK = auto()

    def get_opposite(self) -> "Colour":
        if self == Colour.WHITE:
            return Colour.BLACK
        elif self == Colour.BLACK:
            return Colour.WHITE

    def __repr__(self):
        if self == Colour.WHITE:
            return "Colour.WHITE"
        elif self == Colour.BLACK:
            return "Colour.BLACK"


@dataclass
class Piece:
    position: Tuple[int, int]  # row, col from top left
    colour: Colour
    is_king: bool = False

    def __copy__(self):
        return Piece(self.position, self.colour, self.is_king)
