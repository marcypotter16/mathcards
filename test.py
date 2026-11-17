import random
from collections.abc import Sequence
from typing import Any

from entities.card.base import BaseCard, CardId
from entities.card.eor_card import RingElementCard
from entities.card.op_card import OperatorCard, OperatorType
from mathematics.base import CommUnitRing
from mathematics.ring import QQ, ZZ, PolyRing, ZZn
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
    game: StateManager,
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
            deck[card_id] = OperatorCard(game, rng.choice(op_types), card_id)
        else:
            ring = rng.choice(rings)
            element = ring.get_random_element()
            deck[card_id] = RingElementCard(game, ring, element, card_id)

    return deck

from entities.game_manager.dataclasses import GameState
from entities.player import PlayerId, PlayerState


def make_game_state2(sm: StateManager, me: PlayerId = "p1", op: PlayerId = "p2") -> GameState:
    from entities.board import Board
    from entities.card.eor_card import RingElementCard
    from entities.card.op_card import OperatorCard, OperatorType
    from entities.card.spell_card import SpellCard
    from entities.deck import Deck
    from entities.discard_pile import DiscardPile
    from entities.hand import Hand
    from mathematics.base import Category
    from mathematics.poly import Polynomial
    from mathematics.ring import QQ, ZZ, Frac, PolyRing
    """
    Build a deterministic GameState where:
      * `me` has one card of each kind in hand:
          - integer       2   (in ZZ)
          - rational      3/2 (in QQ)
          - polynomial    1+x (in ZZ[x])
          - op card       +
          - op card       *
          - spell         localize
      * `me`'s deck is stocked with a small variety of cards
      * `op`'s deck is stocked as well (so turn simulation works)
      * Boards are empty
      * It's `me`'s turn with 3 actions.
    """
    cards: dict[int, BaseCard] = {}

    def _register(c: BaseCard) -> BaseCard:
        cards[c.card_id] = c
        return c

    # ------------------------------------------------------------------ rings
    zz      = ZZ()
    qq      = QQ()
    zz_x    = PolyRing(zz)      # ZZ[x] — adjust ctor if yours takes a gen name

    # ------------------------------------------------------------------ my hand: one per type
    # 1. Integer card: 2 in ZZ
    integer_card = _register(RingElementCard(sm, zz, 2))

    # 2. Rational card: 3/2 in QQ
    rational_card = _register(RingElementCard(sm, qq, Frac(3, 2)))

    # 3. Polynomial card: 1 + x in ZZ[x]
    poly_value = Polynomial({0: 1, 1: 1}, zz)
    poly_card  = _register(RingElementCard(sm, zz_x, poly_value))

    # 4. Addition operator
    add_card = _register(OperatorCard(sm, OperatorType.ADD))

    # 5. Multiplication operator
    mul_card = _register(OperatorCard(sm, OperatorType.MUL))

    # 6. Localize spell
    localize_card = _register(SpellCard(sm, "localize"))

    cc_card = _register(SpellCard(sm, "category cring"))

    invert_card = _register(OperatorCard(sm, OperatorType.INVERT))

    my_hand_ids = [
        integer_card.card_id,
        rational_card.card_id,
        poly_card.card_id,
        add_card.card_id,
        mul_card.card_id,
        localize_card.card_id,
        cc_card.card_id,
        invert_card.card_id
    ]

    # ------------------------------------------------------------------ my deck: a bit of everything
    def _new_eor(ring, value) -> int:
        return _register(RingElementCard(sm, ring, value)).card_id

    def _new_op(op) -> int:
        return _register(OperatorCard(sm, op)).card_id

    def _new_spell(name: str) -> int:
        return _register(SpellCard(sm, name)).card_id

    my_deck_ids = [
        _new_eor(zz, 3),
        _new_eor(zz, 5),
        _new_eor(qq, Frac(1, 2)),
        _new_eor(qq, Frac(5, 3)),
        _new_eor(zz_x, Polynomial({0: 1, 2: 1}, zz)),   # 1 + x^2
        _new_eor(zz_x, Polynomial({1: 2}, zz)),          # 2x
        _new_op(OperatorType.SUB),
        _new_op(OperatorType.INVERT),
        _new_spell("localize"),
        _new_spell("category cring")
    ]

    # ------------------------------------------------------------------ opponent: ditto, so turn flow doesn't break
    op_deck_ids: list[int] = [
        _new_eor(zz, 7),
        _new_eor(qq, Frac(2, 5)),
        _new_eor(zz_x, Polynomial({0: 3, 1: 1}, zz)),    # 3 + x
        _new_op(OperatorType.ADD),
        _new_op(OperatorType.MUL),
        _new_spell("localize"),
    ]

    # ------------------------------------------------------------------ player states
    me_state = PlayerState(
        id      = me,
        board   = Board(),
        hand    = Hand(),
        deck    = Deck(),
        discard = DiscardPile([]),
        money   = 0.0,
        items   = [],
    )
    me_state.hand.cards = my_hand_ids
    me_state.deck.cards = my_deck_ids

    op_state = PlayerState(
        id      = op,
        board   = Board(),
        hand    = Hand(),
        deck    = Deck(),
        discard = DiscardPile([]),
        money   = 0.0,
        items   = [],
    )
    op_state.deck.cards = op_deck_ids

    # ------------------------------------------------------------------ game state
    return GameState(
        players         = {me: me_state, op: op_state},
        boards          = {me: me_state.board, op: op_state.board},
        cards           = cards,
        active_ring     = zz,
        active_category = Category.AbGp,
        turn            = me,
        n_actions_left  = 3,
        rng_seed        = 0,
    )

# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tfr = TypstFormulaRenderer()
    game = StateManager(tfr)
    deck = create_deck(20, game, op_ratio=0.3, seed=42)

    for cid, card in deck.items():
        print(cid, "->", card)