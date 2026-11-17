from collections.abc import Callable
from typing import TYPE_CHECKING, TypedDict

from entities.card.eor_card import RingElementCard
from entities.game_manager.actions import ChangeRingAction
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId
from mathematics.base import Category
from mathematics.ring import LocalizationElement
from mathematics.serialization import serialize_ring

if TYPE_CHECKING:
    from entities.card.base import CardId
    from entities.game_manager.dataclasses import GameState


def localize_action(gs: GameState, targets: list[CardId], actor: PlayerId):
    target = targets[0]
    card = gs.cards[target]
    if not isinstance(card, RingElementCard):
        raise TypeError("Can only localize with respect to a RingElementCard")
    if not gs.active_ring.validate_element(card.current_value):
        raise ValueError(f"It appears {card.current_value} is not an element of {gs.active_ring}")
    gs.active_ring = LocalizationElement(gs.active_ring, card.current_value)
    EVENT_BUS.emit(ChangeRingAction(actor, serialize_ring(gs.active_ring)))

def can_apply_localize(gs: GameState, targets: list[CardId], actor: PlayerId) -> tuple[bool, str | None]:
    if gs.active_category not in { Category.CRing }:
        return False, "localization requires CRing category"
    if len(targets) != 1:
        return False, "localize requires exactly one target"
    target_card = gs.cards[targets[0]]
    if not hasattr(target_card, "current_value"):
        return False, "localize target must be a ring element card"
    if not gs.active_ring.validate_element(target_card.current_value):
        return False, (
            f"{target_card.current_value} is not an element of "
            f"{gs.active_ring}"
        )
    return True, None

def category_cring_action(gs: GameState, targets: list[CardId], actor: PlayerId):
    gs.active_category = Category.CRing

def can_apply_category_cring(gs: GameState, targets: list[CardId], actor: PlayerId) -> tuple[bool, str | None]:
    return True, None


# Define type aliases for readability
type ActionFn = Callable[[GameState, list[CardId], PlayerId], None]
type CanApplyFn = Callable[[GameState, list[CardId], PlayerId], tuple[bool, str | None]]

# Define the exact structure of the inner dictionary
class SpellHandler(TypedDict):
    action: ActionFn
    can_apply: CanApplyFn

# Use it in your main dictionary
SPELL_ACTIONS: dict[str, SpellHandler] = {
    "localize": {
        "action": localize_action,
        "can_apply": can_apply_localize,
    },
    "category cring": {
        "action": category_cring_action,
        "can_apply": can_apply_category_cring
    }
}


SPELL_TYPST = {
    "localize": "R_x",
    "category cring": "\"CRing\""
}