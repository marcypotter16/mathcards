from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any

from entities.board.BoardManager import BoardManager
from entities.hand.HandManager import HandManager

class ActionType(Enum):
    PLAY_CARD_FROM_HAND     = auto()
    ATTACK_TARGET           = auto()
    END_TURN                = auto()
    DRAW_CARD               = auto()

@dataclass
class GameAction:
    action_type:    ActionType
    player_id:      str                          # Who is performing the action ('player_1', 'opponent', etc.)
    payload:        dict[str, Any] = field(default_factory=dict)  # Card IDs, target slots, coordinates, etc.

    def to_dict(self) -> dict:
        """Converts action to a JSON-serializable dictionary for networking."""
        return {
            "action_type": self.action_type.name,
            "player_id": self.player_id,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameAction":
        """Reconstructs an action received from the server."""
        return cls(
            action_type=ActionType[data["action_type"]],
            player_id=data["player_id"],
            payload=data["payload"]
        )