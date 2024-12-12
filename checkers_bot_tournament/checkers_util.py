from math import inf, log10
from typing import overload

from checkers_bot_tournament.bots.base_bot import Bot
from checkers_bot_tournament.bots.bot_tracker import BotTracker


@overload
def make_unique_bot_string(idx: int, bot: str) -> str: ...


@overload
def make_unique_bot_string(bot: Bot) -> str: ...


@overload
def make_unique_bot_string(bot: BotTracker) -> str: ...


def make_unique_bot_string(*args, **kwargs) -> str:
    """
    This exists because we can have multiple of the same bot playing each other
    so we need a way to differentiate them.
    """
    # Runtime implementation:
    if len(args) == 1 and isinstance(args[0], Bot):
        bot = args[0]
        return f"[{bot.bot_id}] {bot.get_name()}"
    elif len(args) == 1 and isinstance(args[0], BotTracker):
        bot = args[0].bot
        return f"[{bot.bot_id}] {bot.get_name()}"
    elif len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], str):
        idx, bot_str = args
        return f"[{idx}] {bot_str}"
    else:
        raise TypeError("Invalid arguments to make_unique_bot_string")


# Function to compute Performance Rating of player against a specific
# opponent given both Elo ratings
def compute_performance_rating(w: int, d: int, l: int, bot_rating: float, opp_rating: float):
    # https://en.wikipedia.org/wiki/Performance_rating_(chess)
    # For player A with total score s_A over a series of n games,
    # with w wins, d draws, and l losses, and opponent ratings
    # R_i(R_1, R_2, ..., R_n), the perfect
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
    #     = R_opp - 400 * log10((1/p) - 1), where p is the % perf s_A/n.

    total = w + d + l
    if total == 0:
        return None, None  # no games
    score = w + 0.5 * d
    p = score / total
    if p == 0:
        # If never scored anything, p=0, D -> -infinity.
        D = -inf
    elif p == 1:
        # If always won, p=1 means D -> +infinity.
        D = inf
    else:
        D = -400.0 * log10((1.0 / p) - 1.0)
        # Bound D between -800 and 800 if not inf
        D = min(800.0, D)
        D = max(-800.0, D)

    perf_rating = opp_rating + D
    diff = perf_rating - bot_rating
    return perf_rating, diff
