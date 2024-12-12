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

    @property
    def total_wins(self):
        return self.white_wins + self.black_wins

    @property
    def total_draws(self):
        return self.white_draws + self.black_draw

    @property
    def total_losses(self):
        return self.white_losses + self.black_losses

    @property
    def total_games(self):
        return self.total_wins + self.total_draws + self.total_losses


STARTING_ELO = 1500
# Dynamic learning rate as per USCF: K = 800/(Ne + m),
# where Ne is effective number of games a player's rating is based on, and
# m the number of games the player completed in a tournament for rating consideration

# Each multiple of scale rating difference is a 10x increase in expected score
SCALE = 400


class BotTracker:
    def __init__(self, bot: Bot, unique_bot_names: list[str]) -> None:
        self.bot = bot
        self.rating: float = STARTING_ELO
        self.stats = GameResultStat()
        self.h2h_stats: dict[str, GameResultStat] = {
            unique_bot_name: GameResultStat() for unique_bot_name in unique_bot_names
        }

        self.games_played = 0

        # resets every tournament
        self.tournament_evs: list[float] = []
        self.tournament_scores: list[float] = []

    def calculate_ev(self, other: "BotTracker") -> float:
        Qa = 10 ** (self.rating / SCALE)
        Qb = 10 ** (other.rating / SCALE)

        Ea = Qa / (Qa + Qb)  # Ea + Eb = 1
        return Ea

    def register_ev(self, ev: float) -> None:
        self.tournament_evs.append(ev)

    def _register_result(self, score: float) -> None:
        self.tournament_scores.append(score)

    def register_game_result(self, game_result: GameResult):
        from checkers_bot_tournament.checkers_util import make_unique_bot_string

        unique_name = make_unique_bot_string(self.bot)
        white_score_lookup = {Result.WHITE: 1, Result.BLACK: 0, Result.DRAW: 0.5}

        match unique_name:
            case game_result.white_name:
                # Bot is playing as White
                self._register_result(white_score_lookup[game_result.result])
                if game_result.result == Result.WHITE:
                    # Bot won as White
                    self.stats.white_wins += 1
                    self.h2h_stats[game_result.black_name].white_wins += 1
                elif game_result.result == Result.BLACK:
                    # Bot lost as White
                    self.stats.white_losses += 1
                    self.h2h_stats[game_result.black_name].white_losses += 1
                elif game_result.result == Result.DRAW:
                    # Bot drew as White
                    self.stats.white_draws += 1
                    self.h2h_stats[game_result.black_name].white_draws += 1
                else:
                    raise ValueError(f"Unknown game result: {game_result.result}")

            case game_result.black_name:
                # Bot is playing as Black
                self._register_result(1 - white_score_lookup[game_result.result])
                if game_result.result == Result.BLACK:
                    # Bot won as Black
                    self.stats.black_wins += 1
                    self.h2h_stats[game_result.white_name].black_wins += 1
                elif game_result.result == Result.WHITE:
                    # Bot lost as Black
                    self.stats.black_losses += 1
                    self.h2h_stats[game_result.white_name].black_losses += 1
                elif game_result.result == Result.DRAW:
                    # Bot drew as Black
                    self.stats.black_draws += 1
                    self.h2h_stats[game_result.white_name].black_draws += 1
                else:
                    raise ValueError(f"Unknown game result: {game_result.result}")

            case _:
                # Bot's unique name does not match either player in the game result
                raise ValueError(
                    f"Unknown bot name {unique_name} does not match "
                    f"{game_result.white_name=} or {game_result.black_name=}"
                )

    def update_rating(self) -> None:
        assert len(self.tournament_evs) == len(self.tournament_scores), (
            f"{self.tournament_evs} {self.tournament_scores}"
            "You are supposed to call this after registering all tournament results"
        )

        tournament_games_played = len(self.tournament_evs)
        total_ev = sum(self.tournament_evs)
        total_score = sum(self.tournament_scores)

        K_FACTOR = 800 / (self.games_played + tournament_games_played)
        self.rating += K_FACTOR * (total_score - total_ev)

        self.games_played += tournament_games_played
        self.tournament_evs = []
        self.tournament_scores = []
