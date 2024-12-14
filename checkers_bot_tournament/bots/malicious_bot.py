from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.play_move_info import PlayMoveInfo


class MaliciousBot(Bot):
    def play_move(self, info: PlayMoveInfo) -> int:
        # Try to mess with the move_history in Board. This should not work.
        # info.board.move_history = []
        return 0

    def get_name(self):
        return "MaliciousBot"
