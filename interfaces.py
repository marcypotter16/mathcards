from enum import Enum
from typing import Protocol

import pyray as rl

from entities.game_manager.actions import CardEndedDragging


class DropResult(Enum):
    Accepted        = 0
    Outside         = 1
    InsideInvalid   = 2

class DropZone(Protocol):
    """An interface for a drop zone (drag and drop)"""
    rect: rl.Rectangle
    def try_accept_drop(self, act: CardEndedDragging) -> DropResult: ...
    