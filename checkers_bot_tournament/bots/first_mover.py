from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class FirstMover(Bot):
    """
    Just picks the first move :D
    """

    def play_move(self, info: PlayMoveInfo) -> int:
        return 0

    def get_name(self) -> str:
        return "FirstMover"
