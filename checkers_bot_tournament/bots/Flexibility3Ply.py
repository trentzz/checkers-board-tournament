from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.board import Board
from checkers_bot_tournament.piece import Colour
from checkers_bot_tournament.move import Move

import copy

class Flexibility3Ply(Bot):
    """
    Maximise the length of my move_list after my opponent's best move
    """
    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        opp_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE

        scores1: list[tuple[int, int]] = []
        for i1, move1 in enumerate(move_list):
            searchboard = copy.deepcopy(board)
            searchboard.move_piece(move1) # Our candidate move, now opp's turn
            move_list_2 = searchboard.get_move_list(opp_colour)

            if len(move_list_2) == 0:
                # Great! This move wins the game.
                return i1

            scores2: list[tuple[int, int]] = []
            for i2, move2 in enumerate(move_list_2):
                searchboard2 = copy.deepcopy(searchboard)
                searchboard2.move_piece(move2) # Opp's candidate move, now our turn

                # Score by number of moves WE can make
                s2 = self.score_board(searchboard2, colour)
                scores2.append((i2, s2,))
            
            # As opp, one would want to minimise our score. Save the i1th move
            # that would achieve this
            min_index2, min_score2 = min(scores2, key=lambda x: x[1])
            scores1.append((i1, min_score2,))

        # Now as ourselves, we want to maximise our score assuming our opp
        # wants to do us as much harm as they can (albeit from by our metrics)
        max_index1, max_score1 = max(scores1, key=lambda x: x[1])

        return max_index1

    def score_board(self, board: Board, colour_to_move: Colour) -> int:
        return len(board.get_move_list(colour_to_move))

    def get_name(self) -> str:
        return "Flexibility3PlyBot"