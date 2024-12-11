import os
from dataclasses import dataclass
from datetime import datetime
from typing import IO, Dict, Optional, Type

from checkers_bot_tournament.board import Board
from checkers_bot_tournament.board_start_builder import (
    BoardStartBuilder,
    DefaultBSB,
    LastRowBSB,
)

# BOT TODO: Import your bot here!
from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker
from checkers_bot_tournament.bots.copycat import CopyCat
from checkers_bot_tournament.bots.first_mover import FirstMover
from checkers_bot_tournament.bots.greedycat import GreedyCat
from checkers_bot_tournament.bots.random_bot import RandomBot
from checkers_bot_tournament.bots.scaredycat import ScaredyCat
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from checkers_bot_tournament.game import Game
from checkers_bot_tournament.game_result import GameResult


@dataclass
class GameResultStat:
    white_wins: int = 0
    white_draws: int = 0
    white_losses: int = 0

    black_wins: int = 0
    black_draws: int = 0
    black_losses: int = 0


class Controller:
    # BOT TODO: Add your bot mapping here!
    bot_mapping: Dict[str, Type[Bot]] = {
        "RandomBot": RandomBot,
        "FirstMover": FirstMover,
        "ScaredyCat": ScaredyCat,
        "GreedyCat": GreedyCat,
        "CopyCat": CopyCat,
    }

    board_start_builder_mapping: Dict[str, Type[BoardStartBuilder]] = {
        "default": DefaultBSB,
        "last_row": LastRowBSB,
    }

    def __init__(
        self,
        mode: str,
        board_start_builder: str,
        pdn: Optional[str],
        bot_name: Optional[str],
        bot_names: list[str],
        size: int,
        rounds: int,
        verbose: bool,
        output_dir: str,
        export_pdn: bool,
    ):
        self.mode = mode

        # NOTE: size currently not used
        self.size = size
        self.board_start_builder: BoardStartBuilder = self._get_board_start_builder(
            board_start_builder
        )

        self.pdn = pdn
        self.bot_name = bot_name

        self.bot_list: list[BotTracker] = self._init_bots(bot_names)

        self.rounds = rounds
        self.verbose = verbose
        self.output_dir = output_dir
        self.export_pdn = export_pdn

        # Inits for non-params
        # List of rounds, each round being a list of games
        self.games: list[list[Game]] = [[] for _ in range(rounds)]
        self.game_results: list[list[GameResult]] = [[] for _ in range(rounds)]
        self.game_id_counter: int = 0
        self.game_results_folder: Optional[str] = None

        self._init_game_schedule()

    def _init_bots(self, bot_names: list[str]) -> list[BotTracker]:
        unrecognised_bots = []
        bot_list: list[BotTracker] = []
        for bot in bot_names:
            if bot not in Controller.bot_mapping:
                unrecognised_bots.append(bot)

        if unrecognised_bots:
            raise ValueError(f"bots: {', '.join(unrecognised_bots)} entered in CLI not recognised!")

        idx_bot_names: list[tuple[int, str]] = [
            (
                idx,
                bot_name,
            )
            for idx, bot_name in enumerate(bot_names)
        ]
        unique_bot_names = list(map(lambda x: make_unique_bot_string(x[0], x[1]), idx_bot_names))
        for idx, bot_name in idx_bot_names:
            bot_class = self.bot_mapping[bot_name]
            bot_list.append(
                BotTracker(bot=bot_class(bot_id=idx), unique_bot_names=unique_bot_names)
            )

        return bot_list

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
                    unique_bot_names = list(map(lambda x: make_unique_bot_string(x), self.bot_list))
                    bot_class = self.bot_mapping[self.bot_name]
                    hero_bot = BotTracker(
                        bot=bot_class(bot_id=-1), unique_bot_names=unique_bot_names
                    )
                except KeyError:
                    raise ValueError(f"bot name {self.bot_name} entered in CLI not recognised!")
                self._init_one_schedule(hero_bot)
            case _:
                raise ValueError(f"mode value {self.mode} not recognised!")

        if self.verbose:
            games_per_round = len(self.games[0])
            total = len(self.games[0]) * self.rounds
            print(f"{len(self.bot_list)} bots registered")
            print(
                f"{games_per_round} double-round-robin games/tourney * {self.rounds} tourneys = {total} games scheduled"
            )

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
        new_game1 = Game(
            bot1,
            bot2,
            Board(self.board_start_builder),
            self._get_new_game_id(),
            rnd,
            self.verbose,
            self.pdn,
        )
        new_game2 = Game(
            bot2,
            bot1,
            Board(self.board_start_builder),
            self._get_new_game_id(),
            rnd,
            self.verbose,
            self.pdn,
        )
        self.games[rnd].append(new_game1)
        self.games[rnd].append(new_game2)

    def _get_new_game_id(self) -> int:
        self.game_id_counter += 1
        return self.game_id_counter

    def _get_board_start_builder(self, board_start_builder: str) -> BoardStartBuilder:
        if board_start_builder not in Controller.board_start_builder_mapping:
            raise ValueError(f"board_state: {board_start_builder} not recognised!")

        board_start_builder_class = Controller.board_start_builder_mapping[board_start_builder]
        return board_start_builder_class(self.size)

    def _create_timestamped_folder(self, prefix: str = "checkers_game_results") -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        folder_name = f"{prefix}_{timestamp}"
        folder_path = os.path.join(self.output_dir, folder_name)

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)
        self.game_results_folder = folder_path

    ###################################
    #  ^^^ Initialising functions ^^^ #
    ###################################

    def run(self) -> None:
        self._create_timestamped_folder()
        for rnd in range(self.rounds):
            for game in self.games[rnd]:
                ev_white = game.white.calculate_ev(game.black)
                ev_black = 1 - ev_white

                # Sum of EV score for each player
                # based on all games they will play in this tournaments
                game.white.register_ev(ev_white)
                game.black.register_ev(ev_black)

            for game in self.games[rnd]:
                game_result = game.run()
                self.game_results[rnd].append(game_result)

            self._write_game_results(self.game_results[rnd])

            # Calculate Elo at the end of all matches in a round
            for game, game_result in zip(self.games[rnd], self.game_results[rnd]):
                game.white.register_game_result(game_result)
                game.black.register_game_result(game_result)

            for bot in self.bot_list:
                bot.update_rating()

            if self.verbose:
                print(f"Round {rnd} completed")

        if self.verbose:
            print("Tournament completed, writing stats")
        self._write_tournament_results()

    def _write_game_result_summary(self, file: IO, game_result: GameResult) -> None:
        file.write(str(game_result))
        file.write("\n" + "=" * 40 + "\n")

    def _write_game_results(self, game_results: list[GameResult]) -> None:
        assert self.game_results_folder is not None
        game_result_summary_path = os.path.join(self.game_results_folder, "game_result_summary.txt")
        with open(game_result_summary_path, "a", encoding="utf-8") as file:
            for game_result in game_results:
                self._write_game_result_summary(file, game_result)
                if game_result.moves:
                    game_result_moves_path = os.path.join(
                        self.game_results_folder, f"game_{game_result.game_id}.txt"
                    )
                    with open(game_result_moves_path, "w", encoding="utf-8") as moves_file:
                        self._write_game_result_summary(moves_file, game_result)
                        moves_file.write("Moves: \n")
                        moves_file.write(game_result.moves)

                if self.export_pdn:
                    game_result_pdn_path = os.path.join(
                        self.game_results_folder, f"game_{game_result}.pdn"
                    )
                    with open(game_result_pdn_path, "w") as pdn_file:
                        pdn_file.write(game_result.moves_pdn)

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
            col_width = 8  # For "Win", "Draw", "Loss" columns

            # Print the header row once per bot
            header = f"{'Win':<{col_width}}{'Draw':<{col_width}}{'Loss':<{col_width}}{'Overall Score':<{col_width}}"
            file.write(f"{'':<{label_width}}{header}\n")

            # Compute Overall stats
            overall_wins = stats.white_wins + stats.black_wins
            overall_draws = stats.white_draws + stats.black_draws
            overall_losses = stats.white_losses + stats.black_losses

            # Organize counts for White, Black, and Overall
            counts = {
                "White": (stats.white_wins, stats.white_draws, stats.white_losses),
                "Black": (stats.black_wins, stats.black_draws, stats.black_losses),
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

    def _write_tournament_h2h_stats(self, file: IO) -> None:
        """
        Writes head-to-head (H2H) statistics in a 2D matrix form.

        For each pair of distinct bots (i, j), we show the combined W/D/L results
        from i's perspective vs j (regardless of color) in the top half of the matrix
        (where j > i). The diagonal and lower half remain blank to avoid duplication.

        Also, calculates a performance rating based on the final ratings of the opponent
        and the score achieved, and shows the difference between that performance rating
        and the bot's own rating.
        """
        from math import log10

        file.write("Head-to-Head Statistics\n")
        file.write("=" * 100 + "\n\n")

        # Extract bot info for indexing
        bots = self.bot_list
        n = len(bots)

        # Prepare headers
        # We'll print a matrix where rows and columns are bots
        # Column headers: each opponent bot
        max_name_len = max(len(make_unique_bot_string(bot)) for bot in bots)
        name_col_width = max_name_len + 8  # some padding for rating
        cell_width = max(30, name_col_width)  # width for each cell to display W/D/L and PerfRating

        # Print top header row
        file.write(" " * name_col_width)  # empty space for the left top corner
        for j in range(n):
            opp_bot = bots[j]
            opp_str = make_unique_bot_string(opp_bot)
            file.write(f"{opp_str} ({round(opp_bot.rating)})".center(cell_width))
        file.write("\n")
        file.write("-" * (name_col_width + n * cell_width) + "\n")

        # Function to compute Performance Rating of player against a specific
        # opponent given both Elo ratings
        def compute_performance_rating(
            w: int, d: int, l: int, bot_rating: float, opp_rating: float
        ):
            # https://en.wikipedia.org/wiki/Performance_rating_(chess)
            # For player A with total score s_A over a series of n games,
            # with w wins, d draws, and l losses,
            # and opponent ratings R_i(R_1, R_2, ..., R_n), the perfect
            # performance rating is the number R_A where the expected score
            # on the right equals the actual score s_A on the left:
            # s_A = w + 0.5 * d; n = w + d + l;
            # s_A = f(R_A) = [sum i to n] E(A),
            #              = [sum i to n] 1/(1 + 10^((R_i - R_A)/400)), by Elo
            #              = n * 1/(1 + 10^((R_opp - R_A)/400)), for a single opp.
            # (s_A/n)^-1   = 1 + 10^((R_opp - R_A)/400),
            # (n/s_A) - 1  = 10^((R_opp - R_A)/400),
            #
            # 400 * log10((n/s_A) - 1) = R_opp - R_A, therefore
            # R_A = R_opp - 400 * log10((n/s_A) - 1),
            #     = R_opp - 400 * log10((1/p) - 1), where p is the perf % s_A/n.

            total = w + d + l
            if total == 0:
                return None, None  # no games
            score = w + 0.5 * d
            p = score / total
            if p == 0:
                # If never scored anything, p=0, D -> -infinity theoretically,
                # but let's cap it:
                D = -800.0
            elif p == 1:
                # If always won, p=1 means D -> +infinity. We'll just cap it:
                D = 800.0
            else:
                D = -400.0 * log10((1.0 / p) - 1.0)
                # Again, bound D between -800 and 800
                D = min(800.0, D)
                D = max(-800.0, D)

            perf_rating = opp_rating + D
            diff = perf_rating - bot_rating
            return perf_rating, diff

        # Print each row
        for i in range(n):
            row_bot = bots[i]
            row_str = f"{make_unique_bot_string(row_bot)} ({round(row_bot.rating)})"

            # We'll build two lines for each row:
            # line1: from row bot perspective (with W/D/L)
            # line2: from column bot perspective (just PR and diff)
            line1 = f"{row_str:<{name_col_width}}"
            line2 = " " * name_col_width  # second line aligned under columns

            for j in range(n):
                if i == j:
                    # Diagonal: no self matches
                    cell_top = " " * 2 + "x" * (cell_width - 4) + " " * 2
                    cell_bottom = " " * 2 + "x" * (cell_width - 4) + " " * 2
                elif j < i:
                    # Lower half: leave blank
                    cell_top = " " * 2 + "-" * (cell_width - 4) + " " * 2
                    cell_bottom = " " * 2 + "-" * (cell_width - 4) + " " * 2
                else:
                    # Top half: show stats
                    row_bot_name = make_unique_bot_string(row_bot)
                    col_bot = bots[j]
                    col_bot_name = make_unique_bot_string(col_bot)

                    # Row perspective stats: row_bot vs col_bot
                    stat_row_vs_col = row_bot.h2h_stats[col_bot_name]
                    w_rc = stat_row_vs_col.white_wins + stat_row_vs_col.black_wins
                    d_rc = stat_row_vs_col.white_draws + stat_row_vs_col.black_draws
                    l_rc = stat_row_vs_col.white_losses + stat_row_vs_col.black_losses

                    # Column perspective stats: col_bot vs row_bot
                    stat_col_vs_row = col_bot.h2h_stats[row_bot_name]
                    w_cr = stat_col_vs_row.white_wins + stat_col_vs_row.black_wins
                    d_cr = stat_col_vs_row.white_draws + stat_col_vs_row.black_draws
                    l_cr = stat_col_vs_row.white_losses + stat_col_vs_row.black_losses

                    print(w_rc, d_rc, l_rc, w_cr, d_cr, l_cr)

                    if (w_rc + d_rc + l_rc) == 0:
                        # No games played between these bots
                        cell_top = "N/A".center(cell_width)
                        cell_bottom = "N/A".center(cell_width)
                    else:
                        # Compute performance ratings
                        # From row bot perspective
                        perf_rc, diff_rc = compute_performance_rating(
                            w_rc, d_rc, l_rc, row_bot.rating, col_bot.rating
                        )

                        # From col bot perspective
                        perf_cr, diff_cr = compute_performance_rating(
                            w_cr, d_cr, l_cr, col_bot.rating, row_bot.rating
                        )

                        if perf_rc is not None and diff_rc is not None:
                            wdl_str = f"{w_rc}/{d_rc}/{l_rc}"
                            perf_str_row = f"PR={round(perf_rc)} (Δ={round(diff_rc):+})"
                            # Calculate available space
                            wdl_formatted = f"{wdl_str:>11}"
                            perf_formatted_row = f"{perf_str_row:<17}"
                            cell_top = f"{wdl_formatted}  {perf_formatted_row}".ljust(cell_width)
                        else:
                            cell_top = "N/A".center(cell_width)

                        if perf_cr is not None and diff_cr is not None:
                            perf_str_col = f"PR={round(perf_cr)} (Δ={round(diff_cr):+})"
                            cell_bottom = f"{'':>11}  {perf_str_col:<17}".ljust(cell_width)
                        else:
                            cell_bottom = "N/A".center(cell_width)

                line1 += cell_top
                line2 += cell_bottom

            # Print the two lines for this row
            file.write(line1 + "\n")
            file.write(line2 + "\n")

        file.write("\n" + "=" * 100 + "\n\n")

    def _write_tournament_results(self) -> None:
        assert self.game_results_folder is not None
        game_result_stats_path = os.path.join(self.game_results_folder, "game_result_stats.txt")

        with open(game_result_stats_path, "w", encoding="utf-8") as file:
            self._write_tournament_result_stats(file)
            self._write_tournament_h2h_stats(file)
