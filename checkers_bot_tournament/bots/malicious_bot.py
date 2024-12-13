from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Colour


class MaliciousBot(Bot):
    def play_move(self, board: Board, colour: Colour, move_list: list[Move]) -> int:
        # Try to mess with the move_history in Board. This should not work.
        board.move_history = []
        return 0

    def get_name(self):
        return "MaliciousBot"
