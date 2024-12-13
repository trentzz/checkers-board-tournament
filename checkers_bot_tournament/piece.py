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


@dataclass
class Piece:
    position: Tuple[int, int]
    colour: Colour
    is_king: bool = False
