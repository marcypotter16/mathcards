import random
from typing import Any, Sequence

from entities.card.base import BaseCard, CardId
from entities.card.eor_card import EORCard
from entities.card.op_card import OpCard, OperatorType
from mathematics.base import CommUnitRing
from mathematics.ring import ZZ, PolyRing, ZZn, QQ
from state_manager import StateManager
from tfr import TypstFormulaRenderer


def _default_rings() -> list[CommUnitRing[Any]]:
    """
    A small, reliably-constructible set of rings to draw EOR cards from.

    NB: FFq is deliberately *excluded*. Its __init__ in the pasted file never
    calls PolyRingQuot.__init__, so ``self.coefficient_ring`` is never set and
    ``get_random_element()`` (inherited from PolyRing) crashes.
    """
    return [
        ZZ(),
        QQ(),
        ZZn(2), ZZn(3), ZZn(5), ZZn(7), ZZn(11), ZZn(13),
        PolyRing(ZZn(2)),
        PolyRing(ZZn(3)),
        PolyRing(QQ()),
    ]

def create_deck(
    n: int,
    game: "StateManager",
    *,
    op_ratio: float = 0.25,
    rings: Sequence[CommUnitRing[Any]] | None = None,
    start_id: CardId = 0,
    seed: int | None = None,
) -> dict[CardId, BaseCard]:
    """
    Create a deck of ``n`` cards, indexed by unique ``CardId``s.

    Parameters
    ----------
    n
        How many cards to build.
    game
        The ``StateManager`` instance that every card will share.
    op_ratio
        Probability (0.0..1.0) that a given card is an ``OpCard``.
    rings
        Rings used for ``EORCard``s. Defaults to a small built-in list.
    start_id
        First id assigned. Ids are consecutive from ``start_id``.
    seed
        Optional seed for reproducible decks.

    Returns
    -------
    dict[CardId, BaseCard]
        ``{start_id: card, start_id + 1: card, ..., start_id + n - 1: card}``
    """
    if n < 0:
        raise ValueError(f"Cannot create a deck with negative size n={n}")
    if not (0.0 <= op_ratio <= 1.0):
        raise ValueError(f"op_ratio must be in [0, 1], got {op_ratio!r}")

    rng = random.Random(seed)

    if rings is None:
        rings = _default_rings()
    if not rings and op_ratio < 1.0:
        raise ValueError("Need at least one ring to produce EOR cards")

    op_types = list(OperatorType)

    deck: dict[CardId, BaseCard] = {}
    for offset in range(n):
        card_id = start_id + offset
        if rng.random() < op_ratio:
            deck[card_id] = OpCard(game, rng.choice(op_types), card_id)
        else:
            ring = rng.choice(rings)
            element = ring.get_random_element()
            deck[card_id] = EORCard(game, ring, element, card_id)

    return deck


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tfr = TypstFormulaRenderer()
    game = StateManager(tfr)
    deck = create_deck(20, game, op_ratio=0.3, seed=42)

    for cid, card in deck.items():
        print(cid, "->", card)