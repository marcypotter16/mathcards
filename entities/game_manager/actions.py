from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Any, Callable, Protocol

from entities.card.base import CardId
from entities.game_manager.dataclasses import GameState, PlayerId


class ActionType(StrEnum):
    PLAY_CARD_FROM_HAND     = auto()
    ATTACK_TARGET           = auto()
    END_TURN                = auto()
    DRAW_CARD               = auto()
    CHANGE_RING             = auto()
    DISCARD_TO_DRAW         = auto()

# entities/game_manager/actions.py

@dataclass(frozen=True)
class PlayCardAction:
    player_id:              PlayerId
    card_id:                CardId

    def can_apply(self, game: GameState) -> tuple[bool, str | None]:
        """Return (True, None) if legal, else (False, reason)."""
        if self.player_id != game.turn:
            return False, "not your turn"
        if self.card_id not in game.cards:
            return False, f"unknown card {self.card_id}"
        if self.card_id not in game.players[self.player_id].hand:
            return False, "card not in hand"
        if game.n_actions_left <= 0:
            return False, "no actions left"
        # ring/category/cell legality ...
        return True, None

    def apply(self, game: GameState) -> None:
        """Apply unconditionally. Caller must have checked can_apply."""
        ...

class Action(Protocol):
    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        return True, None
    
    def apply(self, gs: GameState) -> None:
        return

@dataclass(frozen=True)
class DrawCardAction(Action):
    player_id:              PlayerId

    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        return True, None

    def apply(self, gs: GameState):
        card = gs.players[self.player_id].deck.cards.pop()
        gs.players[self.player_id].hand.insert_card(card)

@dataclass(frozen=True)
class DiscardToDrawAction(Action):
    player_id:              PlayerId
    discard_ids:            tuple[CardId, ...]   # 2 or 3 cards

@dataclass(frozen=True)
class EndTurnAction(Action):
    player_id:              PlayerId

@dataclass(frozen=True)
class ChangeRingAction(Action):
    player_id:              PlayerId
    ring_ser:               dict[str, Any]          # the target ring

@dataclass(frozen=True)
class AttackTargetAction(Action):
    player_id:              PlayerId
    slot:                   str             # the cell being attacked
    # more fields as the attack mechanic firms up

type GameAction = (
    PlayCardAction
    | DrawCardAction
    | DiscardToDrawAction
    | EndTurnAction
    | ChangeRingAction
    | AttackTargetAction
)

@dataclass(frozen=True)
class ActionEnvelope:
    action_type:    ActionType
    action:         GameAction
    schema_version: int = 1

    def to_dict(self) -> dict:
        return {
            "action_type":    self.action_type.name,
            "action":         asdict(self.action),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ActionEnvelope":
        at = ActionType[d["action_type"]]
        payload = d["action"]
        factory = _ACTION_FACTORIES[at]
        return cls(action_type=at, action=factory(payload), schema_version=d.get("schema_version", 1))


_ACTION_FACTORIES: dict[ActionType, Callable[[dict], GameAction]] = {
    ActionType.PLAY_CARD_FROM_HAND: lambda d: PlayCardAction(
                                        player_id=d["player_id"],
                                        card_id=int(d["card_id"]),
                                    ),
    ActionType.DRAW_CARD:      lambda d: DrawCardAction(player_id=d["player_id"]),
}