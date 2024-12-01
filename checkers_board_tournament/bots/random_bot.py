from checkers_board_tournament.bots.base_bot import Bot
from checkers_board_tournament.move import Move
from checkers_board_tournament.board import Board
from random import randint


class RandomBot(Bot):
    def play_move(self, board: Board, colour: str, move_list: list[Move]) -> int:
        return randint(0, len(move_list) - 1)
    
    def get_name(self) -> str:
        return "RandomBot"