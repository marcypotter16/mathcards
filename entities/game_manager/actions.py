from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Protocol

import pyray as rl

from draw_debug import arm_draw_trace, draw_debug
from entities.card.base import BaseCard, CardId
from entities.printer import Printer
from mathematics.serialization import deserialize_ring

if TYPE_CHECKING:
    from entities.discard_pile import DiscardPile
    from entities.game_manager.dataclasses import GameState, PlayerId
from entities.game_manager.events import EVENT_BUS
from mathematics.vector import Vector2


class ActionType(StrEnum):
    PLAY_CARD_FROM_HAND     = auto()
    ATTACK_TARGET           = auto()
    END_TURN                = auto()
    DRAW_CARD               = auto()
    CHANGE_RING             = auto()
    DISCARD_TO_DRAW         = auto()

# entities/game_manager/actions.py

@dataclass(frozen=True)
class Action(Protocol):
    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        return True, None
    
    def apply(self, gs: GameState) -> None:
        return

@dataclass(frozen=True)
class PlayCardToSlotAction:
    player_id:              PlayerId
    card_id:                CardId
    coords:                 tuple[int, int]

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
        if not game.cards[self.card_id].is_slottable:
            return False, "card is not slottable (for now just ring elements are slottable)"
        return True, None

    def apply(self, game: GameState) -> None:
        """Apply unconditionally. Caller must have checked can_apply."""
        game.boards[self.player_id].grid[f"{self.coords[0]},{self.coords[1]}"] = self.card_id
        game.players[self.player_id].hand.cards.remove(self.card_id)
        game.n_actions_left -= 1
        # game.apply_after_action()

@dataclass(frozen=True)
class CardToDiscardPileAction:
    player_id:  PlayerId
    card_id:    CardId
    # No apply! This is only to tell the renderer to put the card inside the gy

    # def apply(self, gs: GameState) -> None:
    #     # Remove card from hand:
    #     gs.players[self.player_id].hand.cards.remove(self.card_id)
    #     gs.players[self.player_id].discard.cards.append(self.card_id)

@dataclass(frozen=True)
class PlayOpCardAction(Action):
    player_id:  PlayerId
    card_id:    CardId
    arguments:  list[CardId]

    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        if self.player_id != gs.turn:
            return False, "not your turn"
        if gs.n_actions_left <= 0:
            return False, "no actions left"
        return True, None

    def apply(self, gs: GameState) -> None:
        me = gs.players[self.player_id]

        # 1. Op card: hand -> gy
        me.hand.cards.remove(self.card_id)
        me.discard.cards.append(self.card_id)
        EVENT_BUS.emit(CardToDiscardPileAction(self.player_id, self.card_id))

        for cid in self.arguments:
            for row in range(me.board.N_ROWS):
                for col in range(me.board.N_COLS):
                    key = f"{row},{col}"
                    if me.board.grid.get(key) == cid:
                        me.board.grid[key] = None
                        me.discard.cards.append(cid)
                        EVENT_BUS.emit(CardToDiscardPileAction(self.player_id, cid))
                        break
                else:
                    continue
                break

        gs.n_actions_left -= 1            
        # TODO: ora come ora vanno nel mio cimitero anche le carte dell' avversario!!
        # (se gioco una op card sulle carte avversarie)

@dataclass(frozen=True)
class PlaySpellCardAction(Action):
    player_id:  PlayerId
    card_id:    CardId
    targets:    list[CardId]

    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        if self.player_id != gs.turn:
            return False, "not your turn"
        if gs.n_actions_left <= 0:
            return False, "no actions left"
        if self.card_id not in gs.players[self.player_id].hand.cards:
            return False, "card not in hand"

        spell_card = gs.cards[self.card_id]
        spell = getattr(spell_card, "spell", None)
        assert spell is not None
        from spell_db import SPELL_ACTIONS

        handler = SPELL_ACTIONS.get(spell)
        if handler is None:
            return False, f"unknown spell: {spell}"
        return handler["can_apply"](gs, self.targets, self.player_id)

    def apply(self, gs: GameState) -> None:
        me = gs.players[self.player_id]
        spell_card = gs.cards[self.card_id]
        spell = getattr(spell_card, "spell", None)
        from spell_db import SPELL_ACTIONS

        handler = SPELL_ACTIONS.get(spell)
        if handler is None:
            reason = f"unknown spell: {spell}"
            Printer.print(reason, color=rl.RED)
            EVENT_BUS.emit(CardShouldSnapBack(spell_card, reason=reason))
            return
        try:
            # Resolve first so a failed effect leaves hand, board, and discard intact.
            handler["action"](gs, self.targets, self.player_id)
        except Exception as error:
            Printer.print(str(error), color=rl.RED)
            EVENT_BUS.emit(CardShouldSnapBack(spell_card, reason=str(error)))
            return

        me.hand.cards.remove(self.card_id)
        me.discard.cards.append(self.card_id)
        EVENT_BUS.emit(CardToDiscardPileAction(self.player_id, self.card_id))
        
        # 3. Action cost
        gs.n_actions_left -= 1
        # gs.apply_after_action()

@dataclass(frozen=True)
class CardRingConverted(Action):
    actor:      PlayerId
    card_id:    CardId
    to_ring:    dict[str, Any]

    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        # c = gs.cards[self.card_id]
        # if not isinstance(c, RingElementCard):
        #     return False, "only ring elements can be converted"
        # r1 = c.ring
        # r2 = gs.active_ring
        # mor = Conversion.try_get(r1, r2)
        # if mor is None:
        #     return False, f"no canonical map from {r1} to {r2}"
        # return True, None
        return True, None
        ### SHOULD BE CHECKED IN RING MANAGER UI ###

    def apply(self, gs: GameState) -> None:
        raise NotImplementedError("CardRingConverted must be applied by MatchManager")

@dataclass(frozen=True)
class CardInserted(Action):
    actor:      PlayerId
    card_id:    CardId

@dataclass(frozen=True)
class OpCardStartResolving(Action):
    actor:      PlayerId
    card_id:    CardId

@dataclass(frozen=True)
class CardEndedDragging(Action):
    card:       BaseCard
    position:   Vector2

@dataclass(frozen=True)
class CardShouldSnapBack(Action):
    card:       BaseCard
    reason:     str     = "Invalid drop"

@dataclass(frozen=True)
class CardStartedDragging(Action):
    card:       BaseCard

@dataclass(frozen=True)
class DrawCardAction(Action):
    player_id:              PlayerId
    amount:                 int         = 1

    def can_apply(self, gs: GameState) -> tuple[bool, str | None]:
        deck = gs.players[self.player_id].deck
        if not deck.can_draw(self.amount):
            return False, f"Deck has {deck.size} cards, trying to draw {self.amount}."
        if gs.turn != self.player_id:
            return False, "Can't draw outside my turn."
        if gs.n_actions_left <= 0:
            return False, "Not enough actions left this turn."
        return True, None

    def apply(self, gs: GameState):
        arm_draw_trace()
        card = gs.players[self.player_id].deck.cards.pop()
        hand_before = list(gs.players[self.player_id].hand.cards)
        gs.players[self.player_id].hand.insert_card(card)
        gs.n_actions_left -= 1
        draw_debug(
            "DrawCardAction.apply",
            f"actor={self.player_id}",
            f"card={card}",
            f"hand_before={hand_before}",
            f"hand_after={gs.players[self.player_id].hand.cards}",
            f"deck_remaining={gs.players[self.player_id].deck.size}",
        )
        EVENT_BUS.emit(CardInserted(self.player_id, card))


@dataclass(frozen=True)
class DiscardToDrawAction(Action):
    player_id:              PlayerId
    discard_ids:            tuple[CardId, ...]   # 2 or 3 cards

@dataclass(frozen=True)
class StartTurnAction(Action):
    player_id:              PlayerId

    def apply(self, gs: GameState) -> None:
        # Printer.print(f"Starting turn for {self.player_id}")
        gs.n_actions_left = 3

@dataclass(frozen=True)
class EndTurnAction(Action):
    player_id:              PlayerId

    def apply(self, gs: GameState) -> None:
        # Printer.print(f"Ending turn for {self.player_id}")
        gs.turn = "p2" if gs.turn == "p1" else "p1"
        EVENT_BUS.emit(StartTurnAction(gs.turn))

@dataclass(frozen=True)
class ChangeRingAction(Action):
    player_id:              PlayerId
    ring_ser:               dict[str, Any]        # the target ring

    def apply(self, gs: GameState) -> None:
        gs.active_ring = deserialize_ring(self.ring_ser)
        

@dataclass(frozen=True)
class AttackTargetAction(Action):
    player_id:              PlayerId
    slot:                   str             # the cell being attacked
    # more fields as the attack mechanic firms up

type GameAction = (
    PlayCardToSlotAction
    | DrawCardAction
    | DiscardToDrawAction
    | EndTurnAction
    | ChangeRingAction
    | AttackTargetAction
)

@dataclass(frozen=True)
class DiscardPileOpenDetail:
    discard_pile:   DiscardPile

class RendererReady:
    pass

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
    def from_dict(cls, d: dict) -> ActionEnvelope:
        at = ActionType[d["action_type"]]
        payload = d["action"]
        factory = _ACTION_FACTORIES[at]
        return cls(action_type=at, action=factory(payload), schema_version=d.get("schema_version", 1))


_ACTION_FACTORIES: dict[ActionType, Callable[[dict], GameAction]] = {
    ActionType.PLAY_CARD_FROM_HAND: lambda d: PlayCardToSlotAction(
                                        player_id=d["player_id"],
                                        card_id=int(d["card_id"]),
                                        coords=tuple(d) # TODO
                                    ),
    ActionType.DRAW_CARD:      lambda d: DrawCardAction(player_id=d["player_id"]),
}
