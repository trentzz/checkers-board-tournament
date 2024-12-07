from random import randint

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.board import Board


class RandomBot(Bot):
    def play_move(self, board: Board, colour: str, move_list: list[Move]) -> int:
        return randint(0, len(move_list) - 1)
    
    def get_name(self) -> str:
        return "RandomBot"