from math import inf
from pprint import pformat

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour, Piece
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class Hunter(Bot):
    """
    Maximise my material after 3 layers of search
    """

    WINNING_ENDGAME_SCORE = 100
    WON_GAME = 1000

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id)
        self.ply = 1

    def play_move(self, info: PlayMoveInfo) -> int:
        colour = info.colour
        board = info.board

        # print(f"Ply {self.ply if colour == Colour.WHITE else self.ply + 1} as {colour}")
        # pieces = 0
        white_pieces = 0
        black_pieces = 0
        for i in board.grid:
            for j in i:
                if not j:
                    continue
                if j.colour == Colour.WHITE:
                    white_pieces += 1
                else:
                    black_pieces += 1

        if white_pieces == 1 or black_pieces == 1:
            depth = 8
        if white_pieces == 2 or black_pieces == 2:
            depth = 6
        elif (white_pieces + black_pieces) <= 12:
            depth = 6
        else:
            depth = 4

        best_idx_line, best_eval = self.minimax(board, depth, -inf, inf, colour)

        best_line: list[Move] = []
        curr_colour = colour
        search_board = board.__copy__()
        for idx in reversed(best_idx_line):
            move = search_board.get_move_list(curr_colour)[idx]
            best_line.append(move)
            search_board.move_piece(move)
            curr_colour = curr_colour.get_opposite()

        info.position_eval_ret = best_eval
        info.custom_str_ret = (
            "Engine line: " + str(best_line) + "\n\n" + pformat(board.grid, compact=True)
        )

        self.ply += 2
        return best_idx_line.pop()

    def minimax(
        self, board: Board, depth: float, alpha: float, beta: float, colour_to_move: Colour
    ) -> tuple[list[int], float]:
        move_list = board.get_move_list(colour_to_move)
        if len(move_list) == 0:
            if colour_to_move == Colour.WHITE:
                return [], -self.WON_GAME - depth  # encourage finishing game earlier
            else:
                return [], self.WON_GAME + depth

        if depth > 0 or move_list[0].removed:
            # Continue searching/finish the capture sequence
            if colour_to_move == Colour.WHITE:
                max_eval = -inf
                max_idx = 0
                max_moves = None
                for idx, move in enumerate(move_list):
                    search_board = board.__copy__()
                    search_board.move_piece(move)
                    moves, evaluation = self.minimax(
                        search_board, depth - 1, alpha, beta, Colour.BLACK
                    )
                    if evaluation > max_eval:
                        max_eval = evaluation
                        max_idx = idx
                        max_moves = moves
                    alpha = max(alpha, max_eval)
                    if alpha >= beta:
                        break
                max_moves = [] if max_moves is None else max_moves
                max_moves.append(max_idx)
                return max_moves, max_eval
            else:
                min_eval = inf
                min_idx = 0
                min_moves = None
                for idx, move in enumerate(move_list):
                    search_board = board.__copy__()
                    search_board.move_piece(move)
                    moves, evaluation = self.minimax(
                        search_board, depth - 1, alpha, beta, Colour.WHITE
                    )
                    if evaluation < min_eval:
                        min_eval = evaluation
                        min_idx = idx
                        min_moves = moves
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        break
                min_moves = [] if min_moves is None else min_moves
                min_moves.append(min_idx)
                return min_moves, min_eval
        else:
            return [], self.static_eval(board)

    def static_eval(self, board: Board) -> float:
        """
        Evaluate board without searching further
        + score favours white pieces // white is the maximising player
        - score favours black pieces
        """

        def rows_to_promote(piece: Piece, board: Board) -> int:
            if piece.colour is Colour.WHITE:
                return piece.position[0] - 0
            else:
                return (board.size - 1) - piece.position[0]

        def get_distance(piece1: Piece, piece2: Piece) -> int:
            return max(
                abs(piece1.position[0] - piece2.position[0]),
                abs(piece1.position[1] - piece2.position[1]),
            )

        def score_man(
            piece: Piece,
            board: Board,
            white_kings: int,
            white_men: int,
            black_kings: int,
            black_men: int,
            base_score: float,
            white_pieces: list[Piece],
            black_pieces: list[Piece],
        ) -> float:
            base = 1.0
            r = rows_to_promote(piece, board)
            match r:
                case 1:
                    base += 1
                case 2:
                    y, x = piece.position
                    deltas = [(-2, -2), (-2, 2), (-2, 2)]
                    if piece.colour is Colour.WHITE:
                        for deltaY, deltaX in deltas:
                            try:
                                promosq_piece = board.grid[deltaY + y][deltaX + x]
                            except IndexError:
                                base -= 0.1
                                continue
                            if promosq_piece is None:
                                base += 0.1
                    else:
                        for deltaY, deltaX in deltas:
                            try:
                                promosq_piece = board.grid[-deltaY + y][deltaX + x]
                            except IndexError:
                                base -= 0.1
                                continue
                            if promosq_piece is None:
                                base += 0.1
                case 3:
                    base += 0.01
                case 4:
                    base += 0.001

            # When we are winning significantly, favour trading
            if piece.colour is Colour.WHITE:
                if (white_kings * 4 + white_men) - (black_kings * 4 + black_men) >= 6:
                    base *= 0.98
                return base
            else:
                if (black_kings * 4 + black_men) - (white_kings * 4 + white_men) >= 6:
                    base *= 0.98
                return -base

        def score_king(
            piece: Piece,
            board: Board,
            white_kings: int,
            white_men: int,
            black_kings: int,
            black_men: int,
            base_score: float,
            white_pieces: list[Piece],
            black_pieces: list[Piece],
        ) -> float:
            base = 4.0

            # Give bonus when there are less kings
            if piece.colour is Colour.WHITE:
                if white_kings == 1:
                    base += 1
                    if black_kings == 0:
                        base += 1
            else:
                if black_kings == 1:
                    base += 1
                    if white_kings == 0:
                        base += 1

            # Give incentive to leave promotion square
            match rows_to_promote(piece, board):
                case 0:
                    base -= 0.5

            # Close down the distance if winning
            white_winning_endgame = base_score >= self.WINNING_ENDGAME_SCORE
            black_winning_endgame = base_score <= -self.WINNING_ENDGAME_SCORE

            if white_winning_endgame and piece.colour is Colour.WHITE:
                closest_dist = min(map(lambda x: get_distance(piece, x), black_pieces))
                base += 1 / closest_dist
            elif black_winning_endgame and piece.colour is Colour.BLACK:
                closest_dist = min(map(lambda x: get_distance(piece, x), white_pieces))
                base += 1 / closest_dist

            return base if piece.colour is Colour.WHITE else -base

        def score_general(
            base_score: float, white_pieces: list[Piece], black_pieces: list[Piece]
        ) -> float:
            material_score = 0.0
            for row in board.grid:
                for piece in row:
                    if piece:
                        if piece.is_king:
                            material_score += score_king(
                                piece,
                                board,
                                white_kings,
                                white_men,
                                black_kings,
                                black_men,
                                base_score,
                                white_pieces,
                                black_pieces,
                            )
                        else:
                            material_score += score_man(
                                piece,
                                board,
                                white_kings,
                                white_men,
                                black_kings,
                                black_men,
                                base_score,
                                white_pieces,
                                black_pieces,
                            )
            return material_score + base_score

        base_score = 0.0
        white_men = 0
        white_kings = 0
        black_men = 0
        black_kings = 0
        white_pieces: list[Piece] = []
        black_pieces: list[Piece] = []

        for row in board.grid:
            for piece in row:
                if piece:
                    if piece.colour is Colour.WHITE:
                        white_pieces.append(piece)
                        if piece.is_king:
                            white_kings += 1
                        else:
                            white_men += 1
                    else:
                        black_pieces.append(piece)
                        if piece.is_king:
                            black_kings += 1
                        else:
                            black_men += 1

        if white_kings >= 3 and black_kings <= 1 and black_men == 0:
            base_score += self.WINNING_ENDGAME_SCORE + 10
        elif white_kings >= 4 and black_kings <= 2 and black_men == 0:
            base_score += self.WINNING_ENDGAME_SCORE
        elif black_kings >= 3 and white_kings <= 1 and white_men == 0:
            base_score -= self.WINNING_ENDGAME_SCORE + 10
        elif black_kings >= 4 and white_kings <= 2 and white_men == 0:
            base_score -= self.WINNING_ENDGAME_SCORE

        return score_general(base_score, white_pieces, black_pieces)

    @classmethod
    def _get_name(cls) -> str:
        return "Hunter"
