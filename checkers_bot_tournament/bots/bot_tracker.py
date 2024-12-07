from dataclasses import dataclass

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.game_result import GameResult, Result

@dataclass
class GameResultStat:
    white_wins: int = 0
    white_draws: int = 0
    white_losses: int = 0

    black_wins: int = 0
    black_draws: int = 0
    black_losses: int = 0

STARTING_ELO = 1500
# Learning rate
K_FACTOR = 32
# Each multiple of scale rating difference is a 10x increase in expected score
SCALE = 400

class BotTracker:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.rating: float = STARTING_ELO
        self.stats = GameResultStat()

    def calculate_ev(self, other: 'BotTracker') -> float:
        Qa = 10**(self.rating / SCALE)
        Qb = 10**(other.rating / SCALE)

        Ea = Qa / (Qa + Qb) # Ea + Eb = 1
        return Ea
    
    def update_rating(self, score: float, ev: float) -> None:
        self.rating += K_FACTOR * (score - ev)
