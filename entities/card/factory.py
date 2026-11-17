from typing import TYPE_CHECKING, Any, Callable

from entities.card.spell_card import SpellCard
from state_manager import StateManager

if TYPE_CHECKING:
    from entities.card.base import BaseCard

from entities.card.base import CardType, ElementCardSer, OperatorCardSer, CardSer, SpellCardSer
from entities.card.eor_card import RingElementCard
from entities.card.op_card import OperatorCard
from tfr import TypstFormulaRenderer

_FACTORIES: dict[type, Callable[[Any, StateManager], BaseCard]] = {
    ElementCardSer:  RingElementCard.from_ser,
    OperatorCardSer: OperatorCard.from_ser,
    SpellCardSer:    SpellCard.from_ser,
}

def card_from_ser(cd: CardSer, game: StateManager) -> BaseCard:
    factory = _FACTORIES.get(type(cd))
    if factory is None:
        raise ValueError(f"unknown card type: {type(cd).__name__}")
    return factory(cd, game)
import itertools
_card_counter = itertools.count(1)

# entities/card/base.py (or wherever CardSer lives)

def card_ser_from_dict(d: dict) -> CardSer: # this is UNUSED
    ct = CardType(d["card_type"])
    if ct == CardType.ELEMENT:
        return ElementCardSer(
            id=d["id"],
            base_element_ser=d["base_element_ser"],
            current_element_ser=d["current_element_ser"],
            ring_ser=d["ring_ser"],
        )
    if ct == CardType.OPERATOR:
        return OperatorCardSer(
            id=d["id"],
            operator=d["operator"],
            arity=d["arity"],
        )
    if ct == CardType.SPELL:
        return SpellCardSer(
            id=d["id"]
        )
    raise ValueError(f"unknown card_type: {ct!r}")

def next_card_id() -> str:
    return f"card_{next(_card_counter)}"