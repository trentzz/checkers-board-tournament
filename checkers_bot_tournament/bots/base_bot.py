from abc import ABC, abstractmethod

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


class Bot(ABC):
    def __init__(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.move_history: list[Move] = []

    def play_move_wrapper(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        """
        Wrapper function for play_move that updates bot's local copy of
        move_history. Called from Game.
        """
        previous_move = board.get_previous_move()
        if previous_move:
            self.move_history.append(previous_move)

        idx = self.play_move(board, colour, move_list)
        self.move_history.append(move_list[idx])
        return idx

    @abstractmethod
    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        """
        Params:
            board       represents the current state of the board
            colour      the colour the bot has to play
            move_list   a list of allowable moves

        Return:
            int         the chosen move from the move_list
        """
        raise RuntimeError("play_move not implemented!")

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns bot's name. Make sure this matches Controller!
        """
        raise RuntimeError("get_name not implemented yet!")
