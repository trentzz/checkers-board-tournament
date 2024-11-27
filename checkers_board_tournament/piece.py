from typing import Tuple


class Piece:
    def __init__(self, position: Tuple[int, int], colour: str, is_king: bool = False):
        self.position = position
        self.colour = colour
        self.is_king = is_king

