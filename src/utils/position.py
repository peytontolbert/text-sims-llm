from dataclasses import dataclass
from typing import Dict, Tuple
from src.utils.constants import Direction

@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def move(self, direction: Direction) -> 'Position':
        moves = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        dx, dy = moves[direction]
        return Position(self.x + dx, self.y + dy) 