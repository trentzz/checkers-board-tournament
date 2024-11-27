from checkers_board_tournament.bots.base_bot import Bot
from checkers_board_tournament.board import Board
class Game:
    def __init__(self, white: Bot, black: Bot, board: Board):
        self.white = white
        self.black = black
        self.board = board
        
    def run(self):
        pass