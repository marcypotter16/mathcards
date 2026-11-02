from enum import Enum

from entities.base import Entity

class PlayerType(Enum):
    ME = 0
    OP = 1

class Player(Entity):
    def __init__(self) -> None:
        super().__init__()