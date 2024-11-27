# checkers-board-tournament

Uhh pretty much the title. Make bots that play checkers, play them against each other :)

# Install

## Prereqs
- Python
- Poetry (Can be installed with `pipx install poetry`)

```bash
$ cd checkers-board-tournament
$ poetry install
$ poetry run checkers -h
```

# Usage

```bash
$ poetry run checkers -h
```

# Adding your own bot

1. Make a new file in the `bots/` folder
2. Make sure it inherits from `BaseBot`. Have a look at other bots for clarification.
3. Add your bot to `main.py`. Again have a look at existing implementation for details.
4. Run `poetry install`. See [Usage](#usage) for more details on how to run.