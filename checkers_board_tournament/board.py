from checkers_board_tournament.piece import Piece
from checkers_board_tournament.move import Move
from typing import Optional, Tuple


class Board:
    def __init__(self, size: int = 8):
        self.size = size  # Note that size must always be even
        self.grid = [[None for _ in range(self.size)]
                     for _ in range(self.size)]
        self.initialise_pieces()

    def initialise_pieces(self) -> None:
        """
        Initialises pieces on the board. The black pieces are from 0 to (half - 1)
        and the white pieces are from (half - 1) to size. There will always be
        a two row gap between the pieces to start with.
        """

        half = int(self.size / 2)
        # Init black pieces
        for row in range(half - 1):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece((row, col), "BLACK")

        # Init white pieces
        for row in range(half + 1, self.size):
            for col in range(self.size):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece((row, col), "WHITE")

    def move_piece(self, move: Move) -> None:
        start_row, start_col = move.start
        end_row, end_col = move.end
        piece = self.grid[start_row][start_col]

        # Perform the move
        self.grid[start_row][start_col] = None
        self.grid[end_row][end_col] = piece
        piece.position = move.end

        # Handle capture
        if move.removed:
            rem_row, rem_col = move.removed
            self.grid[rem_row][rem_col] = None

        # Promote to king
        if (piece.colour == "WHITE" and end_row == 0) or (
            piece.colour == "BLACK" and end_row == self.size - 1
        ):
            piece.is_king = True

    def add_regular_move(self, moves: list[Move], row: int, col: int, dr: int, dc: int):
        end_row, end_col = row + dr, col + dc
        if (self.is_within_bounds(end_row, end_col)
                and self.grid[end_row][end_col] is None):
            moves.append(Move((row, col), (end_row, end_col), None))

    def add_capture_move(self, moves: list[Move], colour: str, row: int, col: int, dr: int, dc: int):
        capture_row, capture_col = row + 2 * dr, col + 2 * dc
        mid_row, mid_col = row + dr, col + dc

        valid_capture_move = (self.is_within_bounds(capture_row, capture_col) and self.grid[capture_row][capture_col] is None
                              and self.grid[mid_row][mid_col] is not None
                              and self.grid[mid_row][mid_col].colour != colour)
        
        if valid_capture_move:
            moves.append(
                Move((row, col), (capture_row, capture_col), (mid_row, mid_col),))

    def get_move_list(self, colour: str) -> list[Move]:
        moves: list[Move] = []

        # Directions for normal pieces
        forward_directions = (
            [(-1, -1), (-1, 1)] if colour == "WHITE" else [(1, -1), (1, 1)]
        )
        # Directions for kings (can move in all four diagonals)
        king_directions = forward_directions + [
            (-d[0], -d[1]) for d in forward_directions
        ]

        for row in range(self.size):
            for col in range(self.size):
                piece = self.get_piece((row, col))
                if piece and piece.colour == colour:
                    directions = (king_directions if piece.is_king else forward_directions)
                    
                    for dr, dc in directions:
                        self.add_regular_move(moves, row, col, dr, dc)
                        self.add_capture_move(moves, colour, row, col, dr, dc)
        
        # Funny rule in checkers, if there is a capture move available, you MUST
        # take it, so here, if there are any capture moves, we filter to only
        # allow captures moves.
        capture_move_available = False
        for move in moves:
            if move.removed:
                capture_move_available = True
                break
        
        if capture_move_available:
            capture_moves = list(filter(lambda move: move.removed is not None, moves))
            return capture_moves
        
        # If no capture moves available, return all moves
        return moves

    def is_within_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Return the piece at a specific position."""
        row, col = position
        return (
            self.grid[row][col]
            if 0 <= row < self.size and 0 <= col < self.size
            else None
        )

    def display(self) -> str:
        # Looks disgusting but yay python
        return (
            "\n".join(
                " ".join(
                    "." if cell is None else (
                        "W" if cell.colour == "WHITE" else "B")
                    for cell in row
                )
                for row in self.grid
            )
            + "\n"
        )
