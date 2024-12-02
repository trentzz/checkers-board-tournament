from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.board import Board
from checkers_bot_tournament.game_result import GameResult
from checkers_bot_tournament.move import Move
from checkers_bot_tournament.piece import Piece
from checkers_bot_tournament.checkers_util import make_unique_bot_string
from typing import Optional


class Game:
    def __init__(
        self,
        white: Bot,
        black: Bot,
        board: Board,
        game_id: int,
        game_round: int,
        verbose: bool,
    ):
        self.white = white
        self.black = black
        self.board = board
        self.game_id = game_id
        self.game_round = game_round
        self.verbose = verbose

        self.current_turn = "WHITE"
        self.move_number = 1
        self.is_first_move = True

        self.game_result = None
        self.moves = "" if verbose else None

    def make_move(self) -> Optional[Move]:
        bot = self.white if self.current_turn == "WHITE" else self.black
        move_list: list[Move] = self.board.get_move_list(self.current_turn)

        if len(move_list) == 0:
            winner_colour = "BLACK" if self.current_turn == "WHITE" else "WHITE"
            # TODO: You can add extra information here (and pass it into write_game_result)
            # and GameResult as needed
            self.write_game_result(winner_colour)
            return None

        # TODO: Add a futures thingo to limit each bot to 10 seconds per move or smth
        # from concurrent.futures import ThreadPoolExecutor
        # with ThreadPoolExecutor() as executor:
        #     future = executor.submit(...)
        #     try:
        #         return future.result(timeout=10)
        #     except TimeoutError:
        #         !!!
        move_idx = bot.play_move(self.board, self.current_turn, move_list)
        if move_idx < 0 or move_idx >= len(move_list):
            bot_string = make_unique_bot_string(bot.bot_id, bot.get_name())
            raise RuntimeError(
                f"bot: {bot_string} has played an invalid move")

        move = move_list[move_idx]
        self.board.move_piece(move)

        if self.verbose:
            self.moves += f"Move {self.move_number}: {self.current_turn}'s turn\n"
            self.moves += f"Moved from {str(move.start)} to {str(move.end)}\n"
            self.moves += self.board.display() + "\n"

        self.move_number += 1

        return move

    def run(self) -> None:
        while True:
            # TODO: Implement chain moves (use is_first_move)
            move = self.make_move()
            if move is None:
                break

            self.swap_turn()

    def write_game_result(self, winner_colour: str) -> None:
        names = {
            "WHITE": make_unique_bot_string(self.white.bot_id, self.white.get_name()),
            "BLACK": make_unique_bot_string(self.black.bot_id, self.black.get_name())
        }

        winner_name = names[winner_colour]
        loser_colour = "BLACK" if winner_colour == "WHITE" else "WHITE"
        loser_name = names[loser_colour]

        self.game_result = GameResult(self.game_id, self.game_round, winner_name, winner_colour,
                                      0, 0, loser_name, loser_colour, 0, 0, self.move_number, self.moves)

    def get_game_result(self) -> GameResult:
        return self.game_result

    def swap_turn(self) -> None:
        if self.current_turn == "WHITE":
            self.current_turn = "BLACK"
        else:
            self.current_turn = "WHITE"

        self.is_first_move = True
