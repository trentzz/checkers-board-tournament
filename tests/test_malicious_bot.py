import pytest

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import DefaultBSB
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.move import IllegalMoveException, Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class MaliciousBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> Move:
        # Try to submit an invalid move
        return Move((1, 0), (4, 5), (5, 3))

    @classmethod
    def _get_name(cls):
        return "MaliciousBot"


def test_malicious_bot_tampering():
    builder = DefaultBSB()

    # Create a board and populate with pieces
    board = Board(builder)
    game = Game(
        BotTracker(FirstMover, 0, []), BotTracker(MaliciousBot, 1, []), board, 0, 0, True, None
    )

    game2 = Game(
        BotTracker(MaliciousBot, 0, []), FirstMover(MaliciousBot, 1, []), board, 0, 0, True, None
    )

    with pytest.raises(IllegalMoveException):
        game.run()

    with pytest.raises(IllegalMoveException):
        game2.run()
