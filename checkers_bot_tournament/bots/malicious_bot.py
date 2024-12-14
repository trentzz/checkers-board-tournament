from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class MaliciousBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> int:
        # Try to mess with the move_history. This should not work.
        x = info.move_history
        if len(x) > 0:
            x[0] = Move((0, 0), (9, 9), [(6, 0)])
            # etc etc.
        return 0

    @classmethod
    def _get_name(cls):
        return "MaliciousBot"
