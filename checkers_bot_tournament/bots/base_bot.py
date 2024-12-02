from checkers_bot_tournament.board import Board
from checkers_bot_tournament.move import Move
class Bot:
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
    
    def play_move(self, board: Board, colour: str, move_list: list[Move]) -> int:
        """
        Params:
            board       represents the current state of the board
            colour      the colour the bot has to play
            move_list   a list of allowable moves
            
        Return:
            int         the chosen move from the move_list
        """
        raise RuntimeError("play_move not implemented!")

    def get_name(self) -> str:
        raise RuntimeError("get_name not implemented yet!")