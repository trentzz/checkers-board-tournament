from typing import Optional, Tuple

from checkers_bot_tournament.board_start_builder import BoardStartBuilder
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece

Grid = list[list[Optional[Piece]]]


class Board:
    def __init__(self, board_start_builder: BoardStartBuilder, size: int = 8):
        self.size = size  # Note that size must always be even
        if size % 2 != 0:
            raise ValueError("Even board sizes only.")

        self.grid: Grid = board_start_builder.build()

    def move_piece(self, move: Move) -> Tuple[int, bool]:
        """
        Assume move is valid
        (i.e. in bounds, piece exists, vacant destination for normal move, or valid capturing move)

        Returns True if capture or promotion occured, else False
        """
        start_row, start_col = move.start
        end_row, end_col = move.end
        piece = self.grid[start_row][start_col]
        assert piece is not None

        # Perform the move
        self.grid[start_row][start_col] = None
        self.grid[end_row][end_col] = piece
        piece.position = move.end

        captures = 0
        promotion = False

        if move.removed:
            captures = len(move.removed)
            for rem_row, rem_col in move.removed:
                self.grid[rem_row][rem_col] = None

        # Promote to king
        if (not piece.is_king) and (
            (piece.colour == Colour.WHITE and end_row == 0)
            or (piece.colour == Colour.BLACK and end_row == self.size - 1)
        ):
            piece.is_king = True
            promotion = True

        return (captures, promotion)

    def add_regular_move(self, moves: list[Move], row: int, col: int, dr: int, dc: int):
        end_row, end_col = row + dr, col + dc
        if self.is_within_bounds(end_row, end_col) and self.grid[end_row][end_col] is None:
            moves.append(Move((row, col), (end_row, end_col), []))

    def add_capture_move(
        self,
        moves: list[Move],
        colour: Colour,
        original_row: int,
        original_col: int,
        directions: list[tuple[int, int]],
    ) -> None:
        def do_DFS(prev_captured_pieces: list[Piece], curr_row: int, curr_col: int) -> None:
            any_capturable = False
            for i, (dr, dc) in enumerate(directions):
                dest_row, dest_col = curr_row + 2 * dr, curr_col + 2 * dc
                if not self.is_within_bounds(dest_row, dest_col):
                    continue

                piece = self.grid[curr_row + dr][curr_col + dc]
                if piece is None:
                    continue

                capturable = (
                    piece.colour is not colour
                    and self.grid[dest_row][dest_col] is None
                    and piece not in prev_captured_pieces
                )

                if capturable:
                    prev_captured_pieces.append(piece)
                    any_capturable = True
                    do_DFS(prev_captured_pieces, dest_row, dest_col)
                    prev_captured_pieces.pop()

            if not any_capturable and prev_captured_pieces:
                # No further captures available from this sq, so this is a
                # leaf node: Make Move obj starting from original row/col
                # and ending here, with all the captures of our ancestors
                # Since x.position is a tuple, this is deep copied
                moves.append(
                    Move(
                        (original_row, original_col),
                        (curr_row, curr_col),
                        list(map(lambda x: x.position, prev_captured_pieces)),
                    )
                )

        do_DFS([], original_row, original_col)

    def is_valid_move(self, colour: Colour, move: Move) -> bool:
        return move in self.get_move_list(colour)

    def get_move_list(self, colour: Colour) -> list[Move]:
        moves: list[Move] = []

        # Directions for normal pieces
        forward_directions = [(-1, -1), (-1, 1)] if colour == Colour.WHITE else [(1, -1), (1, 1)]
        # Directions for kings (can move in all four diagonals)
        king_directions = forward_directions + [(-d[0], -d[1]) for d in forward_directions]

        for row in range(self.size):
            for col in range(self.size):
                piece = self.get_piece((row, col))
                if piece and piece.colour == colour:
                    directions = king_directions if piece.is_king else forward_directions

                    for dr, dc in directions:
                        self.add_regular_move(moves, row, col, dr, dc)
                    self.add_capture_move(moves, colour, row, col, directions)

        # Funny rule in checkers, if there is a capture move available, you MUST
        # take it, so here, if there are any capture moves, we filter to only
        # allow captures moves.
        capture_move_available = any([move.removed for move in moves])
        if capture_move_available:
            capture_moves = list(filter(lambda move: move.removed, moves))
            return capture_moves

        # If no capture moves available, return all moves
        return moves

    def is_within_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get_piece(self, position: Tuple[int, int]) -> Optional[Piece]:
        """Return the piece at a specific position."""
        row, col = position
        return self.grid[row][col] if 0 <= row < self.size and 0 <= col < self.size else None

    def display_cell(self, cell: Optional[Piece], x: int, y: int) -> str:
        if not cell:
            if (x + y) % 2 == 0:
                return " "
            else:
                return "."

        match (cell.colour, cell.is_king):
            case (Colour.WHITE, False):
                return "w"
            case (Colour.WHITE, True):
                return "W"
            case (Colour.BLACK, False):
                return "b"
            case (Colour.BLACK, True):
                return "B"
            case _:
                raise ValueError("Unexpected piece state encountered.")

    def display(self) -> str:
        # Looks disgusting but yay pythom
        return (
            "\n".join(
                " ".join(self.display_cell(cell, x, y) for x, cell in enumerate(row))
                for y, row in enumerate(self.grid)
            )
            + "\n"
        )
