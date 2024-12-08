from abc import ABC
from typing import Optional

from checkers_bot_tournament.piece import Piece, Colour

Grid = list[list[Optional[Piece]]]


class BoardStartBuilder(ABC):
    def __init__(self, size: int) -> None:
        self.size = size

    def build(self) -> Grid:
        raise RuntimeError("build not implemented yet!")


class DefaultBSB(BoardStartBuilder):
    def build(self) -> Grid:
        grid: Grid = [
            [None for _ in range(self.size)]
            for _ in range(self.size)
        ]

        half = int(self.size / 2)
        # Init black pieces
        for row in range(half - 1):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    grid[row][col] = Piece((row, col), Colour.BLACK)

        # Init white pieces
        for row in range(half + 1, self.size):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    grid[row][col] = Piece((row, col), Colour.WHITE)

        return grid


class LastRowBSB(BoardStartBuilder):
    def build(self) -> Grid:
        grid: Grid = [
            [None for _ in range(self.size)]
            for _ in range(self.size)
        ]

        # Init black pieces
        for col in range(self.size):
            if (0 + col) % 2 == 1:
                grid[0][col] = Piece((0, col), Colour.BLACK)

        # Init white pieces
        for col in range(self.size):
            if (self.size - 1 + col) % 2 == 1:
                grid[self.size -
                     1][col] = Piece((self.size - 1, col), Colour.WHITE)

        return grid
