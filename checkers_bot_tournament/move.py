from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    end: tuple[int, int]
    removed: list[tuple[int, int]]

    def __repr__(self) -> str:
        return f"Move({self.start}, {self.end}, {self.removed})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Move):
            return False
        return (
            self.start == other.start
            and self.end == other.end
            and len(self.removed) == len(other.removed)
            and set(self.removed) == set(other.removed)
        )
