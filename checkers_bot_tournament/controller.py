from datetime import datetime

from itertools import chain
import os
from typing import Optional, Dict, Type, IO, Tuple

from checkers_bot_tournament.game import Game
from checkers_bot_tournament.game_result import Result, GameResult
from checkers_bot_tournament.board import Board
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.checkers_util import make_unique_bot_string

# BOT TODO: Import your bot here!
from checkers_bot_tournament.bots.random_bot import RandomBot
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.bots.scaredycat import ScaredyCat
from checkers_bot_tournament.bots.greedycat import GreedyCat
from checkers_bot_tournament.bots.copycat import CopyCat

class Controller:
    def __init__(self, mode: str, bot_name: Optional[str], bot_names: list[str], size: int, rounds: int, verbose: bool, output_dir: str):
        self.mode = mode
        self.bot_name = bot_name
        
        # NOTE: size currently not used
        self.size = size
        self.rounds = rounds
        self.verbose = verbose
        self.output_dir = output_dir
        
        # Inits for non-params
        # List of rounds, each round being a list of games
        self.games: list[list[Game]] = [[] for _ in range(rounds)]
        self.game_id_counter: int = 0
        # self.game_results_folder: Optional[str] = None
        
        # BOT TODO: Add your bot mapping here!
        self.bot_mapping: Dict[str, Type[Bot]] = {
            "RandomBot": RandomBot,
            "FirstMover": FirstMover,
            "ScaredyCat": ScaredyCat,
            "GreedyCat": GreedyCat,
            "CopyCat": CopyCat,
        }

        # NOTE: From design perspective, I think it's better to verify bots at this point
        # using the bot mapping, then keeping a list of bot classes.
        self.bot_list: list[BotTracker] = []
        self._init_bot_names(bot_names)
        self._init_game_schedule()

    def _init_bot_names(self, bot_names: list[str]) -> None:
        for idx, bot_name in enumerate(bot_names):
            try:
                bot_class = self.bot_mapping[bot_name]
                self.bot_list.append(BotTracker(bot=bot_class(bot_id=idx)))
            except KeyError:
                raise ValueError(f"bot name {bot_name} entered in CLI not recognised!")

    def _init_game_schedule(self) -> None:
        match self.mode:
            case "all":
                assert self.bot_name is None, "--player should not be set if running on all mode"
                self._init_all_schedule()
            case "one":
                assert self.bot_name, "--player must be set in one mode"
                try:
                    # Special case: we set the bot id to -1 since the list starts at 0
                    # kinda hacky but uh :D
                    bot_class = self.bot_mapping[self.bot_name]
                    hero_bot = BotTracker(bot_class(bot_id=-1))
                except KeyError:
                    raise ValueError(f"bot name {self.bot_name} entered in CLI not recognised!")
                self._init_one_schedule(hero_bot)
            case _:
                raise ValueError(f"mode value {self.mode} not recognised!")
        
        if self.verbose:
            games_per_round = len(self.games[0])
            total = len(self.games[0]) * self.rounds
            print(f"{games_per_round} double round-robin games/round * {self.rounds} rounds = {total} games scheduled")

    def _init_all_schedule(self) -> None:
        """
        Schedules all bots against each other, where each pairing plays as both sides in each round
        """
        for rnd in range(self.rounds):
            for id1, bot1 in enumerate(self.bot_list):
                for id2, bot2 in enumerate(self.bot_list):
                    if id1 < id2:
                        self._schedule_pair_game(bot1, bot2, rnd)

    def _init_one_schedule(self, hero_bot: BotTracker) -> None:
        """
        Runs the one bot against all bots in the bot list
        """
        for rnd in range(self.rounds):
            for id2, other in enumerate(self.bot_list):
                self._schedule_pair_game(hero_bot, other, rnd)

    def _schedule_pair_game(self, bot1: BotTracker, bot2: BotTracker, rnd: int) -> None:
        new_game1 = Game(bot1, bot2, Board(), self._get_new_game_id(), rnd, self.verbose)
        new_game2 = Game(bot2, bot1, Board(), self._get_new_game_id(), rnd, self.verbose)
        self.games[rnd].append(new_game1)
        self.games[rnd].append(new_game2)
        
    def _get_new_game_id(self) -> int:
        self.game_id_counter += 1
        return self.game_id_counter

    ###################################
    #  ^^^ Initialising functions ^^^ #
    ###################################

    def run(self) -> None:
        self._create_timestamped_folder()
        for rnd in range(self.rounds):
            evs: list[Tuple[float, float]] = []
            for game in self.games[rnd]:
                ev_white = game.white.calculate_ev(game.black)
                ev_black = 1 - ev_white
                evs.append((ev_white, ev_black,))
                game.run()

                # TODO: game_result needs to be refactored this is annoying
                assert game.game_result
                match game.game_result.result:
                    case Result.WHITE:
                        game.white.stats.white_wins += 1
                        game.black.stats.black_losses += 1
                    case Result.BLACK:
                        game.white.stats.white_losses += 1
                        game.black.stats.black_wins += 1
                    case Result.DRAW:
                        game.white.stats.white_draws += 1
                        game.black.stats.black_draws += 1

            self._write_game_results(self.games[rnd])

            # Calculate Elo at the end of all matches in a round
            for game, (ev_white, ev_black) in zip(self.games[rnd], evs):
                assert game.game_result
                lookup = {Result.WHITE: 1, Result.BLACK: 0, Result.DRAW: 0.5}

                game.white.update_rating(lookup[game.game_result.result], ev_white)
                game.black.update_rating(1 - lookup[game.game_result.result], ev_black)

            if self.verbose:
                print(f"Round {rnd} completed")
        
        if self.verbose:
            print("Tournament completed, writing stats")
        self._write_tournament_results()
        
    def _create_timestamped_folder(self, prefix: str = "checkers_game_results") -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        folder_name = f"{prefix}_{timestamp}"
        folder_path = os.path.join(self.output_dir, folder_name)
        
        # Create the folder
        os.makedirs(folder_path, exist_ok=True)
        self.game_results_folder = folder_path
            
    def _write_game_result_summary(self, file: IO, game: Game) -> None:
        file.write(str(game.game_result))
        file.write("\n" + "=" * 40 + "\n")

    def _write_game_results(self, games: list[Game]) -> None:
        game_result_summary_path = os.path.join(self.game_results_folder, "game_result_summary.txt")
        with open(game_result_summary_path, "a", encoding="utf-8") as file:
            for game in games:
                self._write_game_result_summary(file, game)
                if game.moves:
                    game_result_moves_path = os.path.join(self.game_results_folder, f"game_{game.game_id}.txt")
                    with open(game_result_moves_path, "w", encoding="utf-8") as moves_file:
                        self._write_game_result_summary(moves_file, game)
                        moves_file.write("Moves: \n")
                        moves_file.write(game.moves)

    def _write_tournament_result_stats(self, file: IO) -> None:
        """
        Writes game result statistics to a file in a structured and readable format.
        
        The format includes a header row followed by counts and percentages for
        White, Black, and Overall statistics for each bot.

        Shamelessly crafted with ChatGPT :)
        
        Args:
            file: The file object to write the statistics to.
            game_stats (Dict[str, GameResultStat]): A dictionary mapping bot names to their game statistics.
        """
        file.write("Game Statistics\n")
        file.write("=" * 60 + "\n\n")

        for bot in self.bot_list:
            stats = bot.stats
            file.write(f"Bot Name: {make_unique_bot_string(bot)} ({round(bot.rating)})\n")
            file.write("-" * 60 + "\n")

            label_width = 10  # For "White", "Black", "Overall"
            col_width = 8     # For "Win", "Draw", "Loss" columns

            # Print the header row once per bot
            header = f"{'Win':<{col_width}}{'Draw':<{col_width}}{'Loss':<{col_width}}"
            file.write(f"{'':<{label_width}}{header}\n")

            # Compute Overall stats
            overall_wins = stats.white_wins + stats.black_wins
            overall_draws = stats.white_draws + stats.black_draws
            overall_losses = stats.white_losses + stats.black_losses

            # Organize counts for White, Black, and Overall
            counts = {
                "White":   (stats.white_wins, stats.white_draws, stats.white_losses),
                "Black":   (stats.black_wins, stats.black_draws, stats.black_losses),
                "Overall": (overall_wins, overall_draws, overall_losses),
            }

            # Print absolute counts
            for label, (w, d, l) in counts.items():
                counts_str = f"{w:<{col_width}}{d:<{col_width}}{l:<{col_width}}"
                file.write(f"{label:<{label_width}}{counts_str}\n")

            # Calculate and print percentages
            for label, (w, d, l) in counts.items():
                total_games = w + d + l
                if total_games > 0:
                    win_pct = (w / total_games) * 100
                    draw_pct = (d / total_games) * 100
                    loss_pct = (l / total_games) * 100
                    score_pct = ((w + 0.5 * d) / total_games) * 100
                else:
                    win_pct = draw_pct = loss_pct = score_pct = 0.0

                # Format each percentage including the % sign within the column
                win_str = f"{win_pct:.1f}%"
                draw_str = f"{draw_pct:.1f}%"
                loss_str = f"{loss_pct:.1f}%"
                score_str = f"{score_pct:.2f}%"

                pct_str = (
                    f"{label:<{label_width}}"
                    f"{win_str:<{col_width}}"
                    f"{draw_str:<{col_width}}"
                    f"{loss_str:<{col_width}}"
                    f"= {score_str}"
                )
                file.write(pct_str + "\n")

            file.write("=" * 60 + "\n\n")

    def _write_tournament_results(self) -> None:
        game_result_stats_path = os.path.join(self.game_results_folder, "game_result_stats.txt")
        
        # game_result_map: Dict[str, GameResultStat] = {}
        # if self.bot_name:
        #     game_result_map[make_unique_bot_string(-1, self.bot_name)] = GameResultStat()
        # for bot in self.bot_list:
        #     game_result_map[make_unique_bot_string(bot)] = GameResultStat()

        # for game in chain.from_iterable(self.games):
        #     game_result = game.game_result
        #     assert game_result

        #     match game_result.result:
        #         case Result.WHITE:
        #             game_result_map[game_result.white_name].white_wins += 1
        #             game_result_map[game_result.black_name].black_losses += 1
        #         case Result.BLACK:
        #             game_result_map[game_result.white_name].white_losses += 1
        #             game_result_map[game_result.black_name].black_wins += 1
        #         case Result.DRAW:
        #             game_result_map[game_result.white_name].white_draws += 1
        #             game_result_map[game_result.black_name].black_draws += 1
            
        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            self._write_tournament_result_stats(file)
