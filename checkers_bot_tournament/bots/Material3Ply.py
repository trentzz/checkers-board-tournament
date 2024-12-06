from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.board import Board
from checkers_bot_tournament.piece import Colour
from checkers_bot_tournament.move import Move

import copy

class Material3Ply(Bot):
    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id)
        self.ply = 1

        self.man_value = 2
        self.king_value = 5

    """
    Maximise the length of my move_list after my opponent's best move
    """
    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        print(f"Ply {self.ply if colour == Colour.WHITE else self.ply + 1} as {colour}")
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
            
            print(f"{scores2=}")
            # As opp, one would want to minimise our score. Save the i1th move
            # that would achieve this
            min_index2, min_score2 = min(scores2, key=lambda x: x[1])
            scores1.append((i1, min_score2,))

        # Now as ourselves, we want to maximise our score assuming our opp
        # wants to do us as much harm as they can (albeit from by our metrics)
        max_index1, max_score1 = max(scores1, key=lambda x: x[1])
        print(f"{scores1=}")

        self.ply += 2
        return max_index1

    def score_board(self, board: Board, colour_to_move: Colour) -> int:
        # Determine the letter representing the opponent's pieces
        opp_colour = Colour.BLACK if colour_to_move == Colour.WHITE else Colour.WHITE
        print(colour_to_move, opp_colour)

        # Calculate the material count for the player's pieces
        material_score = 0
        for i in board.grid:
            for j in i:
                if j:
                    if self.ply == 1:
                        print (j.colour, j.is_king, material_score)
                        print(j.colour == colour_to_move, j.colour == opp_colour)
                    match (j.colour, j.is_king):
                        case (opp_colour, True):
                            material_score -= 5
                        case (opp_colour, False):
                            material_score -= 2
                        case (colour_to_move, True):
                            material_score += 4
                        case (colour_to_move, False):
                            material_score += 2
                        case _:
                            assert False

        # Return the difference in material count
        print(material_score)
        return -material_score

    def get_name(self) -> str:
        return "Material3PlyBot"