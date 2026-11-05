from typing import TYPE_CHECKING, Any, Callable

from game import Game

if TYPE_CHECKING:
    from entities.card.base import BaseCard

from entities.card.base import CardType, ElementCardSer, OperatorCardSer, CardSer
from entities.card.eor_card import EORCard
from entities.card.op_card import OpCard
from tfr import TypstFormulaRenderer

_FACTORIES: dict[type, Callable[[Any, Game], BaseCard]] = {
    ElementCardSer:  EORCard.from_ser,
    OperatorCardSer: OpCard.from_ser,
}

def card_from_ser(cd: CardSer, game: Game) -> BaseCard:
    factory = _FACTORIES.get(type(cd))
    if factory is None:
        raise ValueError(f"unknown card type: {type(cd).__name__}")
    return factory(cd, game)
import itertools
_card_counter = itertools.count(1)

# entities/card/base.py (or wherever CardSer lives)

def card_ser_from_dict(d: dict) -> CardSer:
    ct = CardType(d["card_type"])   # "ELEMENT" or "OPERATOR" -> enum
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
    raise ValueError(f"unknown card_type: {ct!r}")

def next_card_id() -> str:
    return f"card_{next(_card_counter)}"