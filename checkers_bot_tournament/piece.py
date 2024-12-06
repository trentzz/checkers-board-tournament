from typing import Tuple, Literal

from enum import auto, Enum

class Colour(Enum):
    WHITE = auto()
    BLACK = auto()

class Piece:
    def __init__(self, position: Tuple[int, int], colour: Colour, is_king: bool = False):
        self.position = position
        self.colour = colour
        self.is_king = is_king

