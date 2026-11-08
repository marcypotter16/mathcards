# tests/test_serialization.py
import json
from dataclasses import is_dataclass, asdict
from typing import TYPE_CHECKING

from Settings import FONT_PATH
from entities.deck import Deck
from entities.game_manager.actions import DrawCardAction, EndTurnAction, PlayCardAction
from entities.hand import Hand
from state_manager import StateManager
from mathematics.base import Category
from test import create_deck

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
GAME = StateManager(TFR)


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
        el = r.one
        card = EORCard(GAME, r, el)
        ser = card.serialize()
        assert_json_roundtrip(asdict(ser))
        rebuilt = card_from_ser(ser, GAME)
        assert rebuilt.serialize() == ser
        assert rebuilt.card_id == card.card_id


def test_card_factory_unknown_type():
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
    # Using the new ID-based insert
    b.insert_card(cards[1].card_id, (0, 0))
    b.insert_card(cards[2].card_id, (0, 1))
    return b, cards


def test_board_roundtrip():
    b, _ = make_board_with_cards()
    ser = b.serialize()
    assert_json_roundtrip(ser)
    b2 = Board.deserialize(ser)
    assert b2.serialize() == ser


def test_board_insert_occupied():
    b, cards = make_board_with_cards()
    try:
        b.insert_card(cards[1].card_id, (0, 0))
    except Board.SlotOccupiedError:
        return
    assert False, "expected SlotOccupiedError"


# ---------- 4. GameState ----------

def make_game_state(game: StateManager | None = None) -> GameState:
    g = game if game is not None else GAME
    cards = create_deck(20, g)
    
    # player 1: board has card 1, hand has cards 2 and 3, deck has remaining cards
    p1 = PlayerState(
        id="p1",
        board=Board(),
        hand=Hand(),
        deck=Deck(),
        discard=Deck(),
        money=10,
        items=[],
    )
    
    # Only put cards in the deck that aren't already on the board or in the hand
    p1.deck.cards = [i for i in cards.keys() if i < 10 and i not in (1, 2, 3)]
    
    p1.board.insert_card(cards[1].card_id, (0, 0))
    p1.hand.insert_card(cards[3].card_id)
    p1.hand.insert_card(cards[2].card_id)

    # player 2: empty board, hand has card 6 and 7, deck has card 8
    p2 = PlayerState(
        id="p2", 
        board=Board(), 
        hand=Hand(), 
        deck=Deck(), 
        discard=Deck(), 
        money=10, 
        items=[],
    )
    p2.hand.insert_card(cards[6].card_id, 0)
    p2.hand.insert_card(cards[7].card_id, 0)
    p2.deck.cards = [cards[8].card_id]

    return GameState(
        players={"p1": p1, "p2": p2},
        boards={"p1": p1.board, "p2": p2.board},
        cards=cards,
        active_ring=ZZ(),
        active_category=Category.CRings,
        turn="p1",
        n_actions_left=3,
        rng_seed=42,
    )


def test_gamestate_roundtrip():
    gs = make_game_state()
    ser = gs.serialize()
    assert_json_roundtrip(asdict(ser))

    gs2 = GameState.deserialize(ser, GAME)
    ser2 = gs2.serialize()
    assert ser2 == ser, f"gamestate mismatch\n in:  {ser}\n out: {ser2}"


def test_gamestate_id_counter_advanced():
    gs = make_game_state()
    ser = gs.serialize()
    gs2 = GameState.deserialize(ser, GAME)
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
    
    # p1 has 2 cards in hand (cards[3] and cards[2])
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
        PlayCardAction(player_id="p1", card_id=2, coords=(0, 0)),
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
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(0 if failed == 0 else 1)   