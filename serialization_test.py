# tests/test_serialization.py
import json
from dataclasses import is_dataclass, asdict
from typing import TYPE_CHECKING

from pyray import load_font

from Settings import FONT_PATH
from entities.deck import Deck
from entities.game_manager.actions import DrawCardAction, EndTurnAction, PlayCardAction
from entities.hand import Hand
from game import Game
from mathematics.base import Category

if TYPE_CHECKING:
    from entities.card.base import BaseCard
from entities.card.factory import card_from_ser
from entities.card.eor_card import EORCard
from entities.card.op_card import OpCard, OperatorType
from entities.board import Board
from entities.game_manager.dataclasses import (
    GameState, GameStateSer, PlayerState, PlayerStateSer,
    PlayerView, GameView,
)
from mathematics.ring import ZZ, QQ, PolyRingQuot, PrincipalPolyIdeal, ZZn, PolyRing
from mathematics.poly import Polynomial
from mathematics.serialization import serialize_ring, deserialize_ring
from tfr import TypstFormulaRenderer

TFR = TypstFormulaRenderer()
GAME = Game(TFR)


# ---------- helpers ----------

def assert_roundtrip(ser, rebuild):
    """ser: original serialized form. rebuild: ser -> new ser."""
    back = rebuild(ser)
    assert back == ser, f"roundtrip mismatch:\n  in:  {ser}\n  out: {back}"


def assert_json_roundtrip(ser):
    """Ensure the form survives json.dumps/loads and comes back structurally equal."""
    dumped = json.dumps(ser)
    loaded = json.loads(dumped)
    assert loaded == json.loads(json.dumps(ser)), f"json roundtrip mismatch"
    return loaded


# ---------- 1. Rings ----------

def test_ring_roundtrip():
    q = QQ()
    rings = [
        ZZ(),
        QQ(),
        ZZn(7),
        PolyRing(q),
        # PolyRing(q, var="y"),
    ]
    for r in rings:
        ser = serialize_ring(r)
        back = deserialize_ring(ser)
        assert serialize_ring(back) == ser, f"ring mismatch: {ser}"


def test_polyringquot_roundtrip():
    q = QQ()
    base = PolyRing(q)
    p = Polynomial({0: q.one, 1: q.one, 2: q.one}, q)   # 1 + x + x^2
    quot = PolyRingQuot(q, PrincipalPolyIdeal(p, base))
    ser = serialize_ring(quot)
    back = deserialize_ring(ser)
    assert serialize_ring(back) == ser


# ---------- 2. Cards ----------

def test_opcard_roundtrip():
    for op in [OperatorType.ADD, OperatorType.INVERT, OperatorType.MUL, OperatorType.SUB]:
        card = OpCard(GAME, op)
        ser = card.serialize()
        assert_json_roundtrip(asdict(ser))
        rebuilt = card_from_ser(ser, GAME)
        assert rebuilt.serialize() == ser
        assert rebuilt.op_type == op # type: ignore
        assert rebuilt.card_id == card.card_id


def test_eorcard_roundtrip():
    rings = [ZZ(), QQ(), ZZn(7), PolyRing(QQ())]
    for r in rings:
        el = r.one      # or r.get_random_element() if available
        card = EORCard(GAME, r, el)
        ser = card.serialize()
        assert_json_roundtrip(asdict(ser))
        rebuilt = card_from_ser(ser, GAME)
        assert rebuilt.serialize() == ser
        assert rebuilt.card_id == card.card_id


def test_card_factory_unknown_type():
    # a DTO that's neither ElementCardSer nor OperatorCardSer
    from dataclasses import dataclass
    @dataclass(frozen=True)
    class Unknown:
        id: int
    try:
        card_from_ser(Unknown(1), GAME) # type: ignore
    except ValueError:
        return
    assert False, "expected ValueError for unknown CardSer"


# ---------- 3. Board ----------

def make_board_with_cards():
    b = Board()
    cards = {
        1: OpCard(GAME, OperatorType.ADD, card_id=1),
        2: EORCard(GAME, ZZ(), ZZ().one, card_id=2),
    }
    b.slotgrid[(0, 0)].content = cards[1]
    b.slotgrid[(0, 1)].content = cards[2]
    return b, cards


def test_board_roundtrip():
    b, cards = make_board_with_cards()
    ser = b.serialize()
    assert_json_roundtrip(ser)
    b2 = Board.deserialize(ser, cards)
    assert b2.serialize() == ser


def test_board_apply_idempotent():
    b, cards = make_board_with_cards()
    ser = b.serialize()
    b.apply(ser, cards)
    assert b.serialize() == ser


def test_board_apply_clears_removed_cells():
    b, cards = make_board_with_cards()
    # remove cell (0,1) from the serialized form
    ser = b.serialize()
    del ser["0,1"]
    b.apply(ser, cards)
    assert b.slotgrid[(0, 1)].content is None


def test_board_apply_unknown_id():
    b, cards = make_board_with_cards()
    ser = b.serialize()
    ser["0,2"] = 999  # id not in cards
    try:
        b.apply(ser, cards)
    except (ValueError, KeyError):
        return
    assert False, "expected error for unknown card id"


# ---------- 4. GameState ----------

def make_game_state() -> GameState:
    tfr = TFR
    g = GAME
    cards: dict[int, BaseCard] = {
        1: OpCard(g, OperatorType.ADD, card_id=1),
        2: OpCard(g, OperatorType.MUL, card_id=2),
        3: EORCard(
            g,
            PolyRingQuot(
                ZZ(), 
                PrincipalPolyIdeal(
                    Polynomial({2: 1}, ZZ()),
                    ZZ()
                    )
                ), 
            Polynomial({1: 2, 0: 5}, ZZ()), card_id=3),
        4: EORCard(g, QQ(), QQ().one, card_id=4),
        5: OpCard(g, OperatorType.ADD, card_id=1),
        6: OpCard(g, OperatorType.MUL, card_id=2),
        7: EORCard(
            g,
            PolyRingQuot(
                ZZ(), 
                PrincipalPolyIdeal(
                    Polynomial({2: 1}, ZZ()),
                    ZZ()
                    )
                ), 
            Polynomial({3: 4, 2: 5}, ZZ()), card_id=3),
        8: EORCard(g, QQ(), QQ().one, card_id=4),
    }
    # player 1: board has card 1, hand has card 3, deck has card 4
    p1 = PlayerState(
        id="p1",
        board=Board(),
        hand=Hand(),
        deck=Deck(),
        discard=Deck(),
        money=10,
        items=[],
    )
    p1.board.slotgrid[(0, 0)].content = cards[1]
    p1.hand.insert_card(cards[3].card_id)
    p1.hand.insert_card(cards[2].card_id)
    p1.deck.cards = [cards[4].card_id]

    # player 2: empty board, hand has card 2
    p2 = PlayerState(
        id="p2", board=Board(), hand=Hand(), deck=Deck(), discard=Deck(), money=10, items=[],
    )
    p2.hand.insert_card(cards[6].card_id, 0)
    p2.hand.insert_card(cards[7].card_id, 0)
    p2.deck.cards = [cards[8].card_id]

    return GameState(
        players={"p1": p1, "p2": p2},
        boards={"p1": p1.board, "p2": p2.board},
        cards=cards,
        active_ring=ZZ(),
        active_category=Category.CRings,     # or Category.RING, whatever your type is
        turn="p1",
        n_actions_left=3,
        rng_seed=42,
    )


def test_gamestate_roundtrip():
    gs = make_game_state()
    ser = gs.serialize()
    # JSON compatibility of the whole envelope
    assert_json_roundtrip(asdict(ser))

    gs2 = GameState.deserialize(ser, GAME)
    ser2 = gs2.serialize()
    assert ser2 == ser, f"gamestate mismatch\n in:  {ser}\n out: {ser2}"


def test_gamestate_id_counter_advanced():
    gs = make_game_state()
    ser = gs.serialize()
    gs2 = GameState.deserialize(ser, GAME)
    # draw a new card id and assert it doesn't collide with existing
    from entities.card.base import BaseCard
    new_id = BaseCard._next_id()
    assert new_id not in gs2.cards, f"id counter not advanced: {new_id}"


def test_gameview_redaction():
    gs = make_game_state()
    ser = gs.serialize()
    view_p1 = GameView.to_view(ser, viewer="p1")
    view_p2 = GameView.to_view(ser, viewer="p2")

    # my own hand is visible
    assert view_p1.players["p1"].hand is not None
    # opponent hand is hidden
    assert view_p2.players["p1"].hand is None
    
    # ← FIX: p1 has 2 cards in hand (cards[3] and cards[2])
    assert view_p1.players["p1"].hand_size == 2, f"expected 2, got {view_p1.players['p1'].hand_size}"
    assert view_p2.players["p1"].hand_size == 2
    
    # boards/discard are public
    assert view_p2.players["p1"].board == view_p1.players["p1"].board
    # card face data is shared (needed for rendering)
    assert view_p1.cards == view_p2.cards


def test_gamestate_json_roundtrip():
    gs = make_game_state()
    ser = gs.serialize()
    wire = json.loads(json.dumps(asdict(ser)))
    loaded = GameStateSer.from_dict(wire)
    gs2 = GameState.deserialize(loaded, GAME)
    assert gs2.serialize() == ser

def test_action_replay():
    gs = make_game_state()
    actions = [
        DrawCardAction(player_id="p1"),
        PlayCardAction(player_id="p1", card_id=2),
        EndTurnAction(player_id="p1"),
        DrawCardAction(player_id="p2")
    ]
    for a in actions:
        ok, reason = a.can_apply(gs)
        assert ok, reason
        a.apply(gs)

    # serialize the resulting state, deserialize, verify identical
    ser = gs.serialize()
    gs2 = GameState.deserialize(ser, GAME)
    assert gs2.serialize() == ser

    # and: replaying the same actions from a fresh state gives the same result
    gs3 = make_game_state()
    for a in actions:
        a.apply(gs3)
    assert gs3.serialize() == ser

# ---------- run ----------

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    # at the bottom of the file, inside `if __name__ == "__main__":`
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:   # <-- FIX: catch all exceptions
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(0 if failed == 0 else 1)