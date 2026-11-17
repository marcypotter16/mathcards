# C:\Users\marcello\Documents\Projects\mathcards\mathcards\entities\game_manager\spell_effects.py
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from entities.card.eor_card import RingElementCard
from entities.game_manager.actions import ChangeRingAction
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId
from mathematics.ring import LocalizationElement
from mathematics.serialization import serialize_ring

if TYPE_CHECKING:
    from entities.card.base import CardId
    from entities.game_manager.dataclasses import GameState

def localize_action(gs: GameState, targets: Sequence[CardId], actor: PlayerId):
    target = targets[0]
    card = gs.cards[target]
    if not isinstance(card, RingElementCard):
        raise TypeError("Can only localize with respect to a RingElementCard")
    if not gs.active_ring.validate_element(card.current_value):
        raise ValueError(f"It appears {card.current_value} is not an element of {gs.active_ring}")
    gs.active_ring = LocalizationElement(gs.active_ring, card.current_value)
    EVENT_BUS.emit(ChangeRingAction(actor, serialize_ring(gs.active_ring)))

# Questo dizionario mappa l'ID stringa preso dal database alla funzione reale
SPELL_REGISTRY: dict[str, Callable[[GameState, Sequence[CardId], PlayerId], None]] = {
    "localize": localize_action,
}
