def make_unique_bot_string(idx: int, bot: str) -> str:
    """
    This exists because we can have multiple of the same bot playing each other
    so we need a way to differentiate them.
    """
    return f"{idx} : {bot}"