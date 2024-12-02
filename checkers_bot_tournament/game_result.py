from dataclasses import dataclass
from typing import Optional

@dataclass
class GameResult:
    game_id: int
    game_round: int
    winner_name: str
    winner_colour: str
    winner_kings_made: int
    winner_num_captures: int
    loser_name: str
    loser_colour: str
    loser_kings_made: int
    loser_num_captures: int
    num_moves: int
    # This is quite chunky (it stores every move and board state) so it's optional
    moves: Optional[str]
    