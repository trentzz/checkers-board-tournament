from typing import Tuple, Literal


class Piece:
    def __init__(self, position: Tuple[int, int], colour: Literal['WHITE', 'BLACK'], is_king: bool = False):
        self.position = position
        self.colour = colour
        self.is_king = is_king

