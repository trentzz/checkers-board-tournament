# checkers-bot-tournament

Uhh pretty much the title. Make bots that play checkers, play them against each other :)

# Install

## Prereqs
- Python
- Poetry (Can be installed with `pipx install poetry`)

```bash
$ cd checkers-bot-tournament
$ poetry install
$ poetry run checkers -h
```

# Usage

```bash
$ poetry run checkers -h
```
## Examples
### Example 1
Run 2 instances of `RandomBot` and 1 instance of `FirstBot` against each other.
- Enable verbose output (which logs the actual moves for each game)
- Set output directory for the run
- Run one round
```bash
$ poetry run checkers RandomBot RandomBot FirstMover --mode all --rounds 1 --verbose --output-dir output
```

# Adding your own bot

1. Fork the repo and make a branch for your bot
2. Make a new file in the `bots/` folder
3. Make sure it inherits from `Bot` in `base_bot.py`. Have a look at other bots for clarification.
4. Add your bot to `controller.py`. Again have a look at existing implementation for details. You can also search for `# BOT TODO`
5. Make sure the string you use in `Controller` and `get_name()` match
6. Run `poetry install`. See [Usage](#usage) for more details and options.
7. Commit and open a PR to the `add-your-bot-here` branch (select your fork as the source, and this repo as the destination)

# Stuff and things

Not an exhaustive list:
- Default size set to an 8x8 board
- If you have the option of capturing a piece, you're forced to (the `move_list` will only contain captures if a capture is available)
- Multiple jumps in one go is not currently supported, I'll do it sometime, but bot implementation shouldn't have to change at all to support it.
- The colours of the pieces are "BLACK" and "WHITE" and white always goes first.
- Each round consists of 2 games where the bots swap being black and white.
- The output consists of a folder with two files: `game_result_stats.txt` and `game_result_summary.txt` as well as all the games as `game_X.txt` if `--verbose` was used.
  - `game_result_stats.txt` is the win/loss of each bot
  - `game_result_summary.txt` is the summary of each game

Finally feel free to open an issue if I did something dumb (very likely).
