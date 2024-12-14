from random import randint

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class RandomBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> int:
        return randint(0, len(info.move_list) - 1)

    @classmethod
    def _get_name(cls) -> str:
        return "RandomBot"
