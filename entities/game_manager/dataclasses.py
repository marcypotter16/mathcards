from enum import StrEnum, Enum, auto
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from entities.card.base import CardId, CardSer, BaseCard
from entities.card.factory import card_from_ser, card_ser_from_dict
from game import Game
from tfr import TypstFormulaRenderer

from entities.hand import Hand
from entities.board import Board
from entities.deck import Deck
from mathematics.base import Category, CommUnitRing

if TYPE_CHECKING:
    from entities.item import Item

from mathematics.serialization import deserialize_ring, serialize_ring


from dataclasses import dataclass

type PlayerId = str

@dataclass(frozen=True)
class ItemSer:
    id:                     str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ItemSer:
        return cls(
            id = d["id"]
        )

@dataclass
class GameState:
    players:            dict[PlayerId, PlayerState]
    boards:             dict[PlayerId, Board]
    cards:              dict[CardId, BaseCard]
    active_ring:        CommUnitRing
    active_category:    Category
    turn:               PlayerId
    n_actions_left:     int
    rng_seed:           int

    def card(self, cid: CardId):
        return self.cards[cid]

    def serialize(self) -> GameStateSer:
        return GameStateSer(
            players         = {pid: pstate.serialize() for pid, pstate in self.players.items()},
            boards          = {pid: b.serialize() for pid, b in self.boards.items()},
            cards           = {pid: c.serialize() for pid, c in self.cards.items()},
            active_ring     = serialize_ring(self.active_ring),
            active_category = self.active_category,
            turn            = self.turn,
            n_actions_left  = self.n_actions_left,
            rng_seed        = self.rng_seed            
        )

    @staticmethod
    def deserialize(gss: GameStateSer, game: Game) -> 'GameState':
        cards = {
            cid: card_from_ser(ser, game) for cid, ser in gss.cards.items()
        }
        if cards:
            BaseCard._set_id_counter(max(cards.keys()) + 1)
        else:
            BaseCard._set_id_counter(1)
        players = {
            pid: PlayerState.deserialize(pss, cards) for pid, pss in gss.players.items()
        }
        boards = {
            pid: Board.deserialize(bss, cards) for pid, bss in gss.boards.items()
        }
        return GameState(
            players         = players,
            boards          = boards,
            cards           = cards,
            active_ring     = deserialize_ring(gss.active_ring),
            active_category = Category(gss.active_category),
            turn            = gss.turn,
            n_actions_left  = gss.n_actions_left,
            rng_seed        = gss.rng_seed
        )


@dataclass(frozen=True)
class GameStateSer:
    players:            dict[PlayerId, PlayerStateSer]
    boards:             dict[PlayerId, dict[str, CardId | None]]
    cards:              dict[CardId, CardSer]
    active_ring:        dict[str, Any]
    active_category:    str
    turn:               PlayerId
    n_actions_left:     int
    rng_seed:           int

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameStateSer":
        return cls(
            players={pid: PlayerStateSer.from_dict(p) for pid, p in d["players"].items()},
            boards={
                pid: {k: (None if v is None else int(v)) for k, v in b.items()}
                for pid, b in d["boards"].items()
            },
            cards={int(cid): card_ser_from_dict(cser) for cid, cser in d["cards"].items()},
            active_ring=d["active_ring"],                       # already a plain dict
            active_category=Category(d["active_category"]),     # "GRP"/"RING" -> enum
            turn=d["turn"],
            n_actions_left=int(d["n_actions_left"]),
            rng_seed=int(d["rng_seed"]),
        )

@dataclass
class PlayerState:
    id:                 PlayerId
    board:              Board
    hand:               Hand      # private
    deck:               Deck
    discard:            Deck
    money:              float
    items:              list[Item]

    def serialize(self) -> PlayerStateSer:
        return PlayerStateSer(
            id      = self.id,
            board   = self.board.serialize(),
            hand    = self.hand.serialize(),
            deck    = self.deck.serialize(),
            discard = self.discard.serialize(),
            money   = self.money,
            items   = [item.serialize() for item in self.items]
        )

    @staticmethod
    def deserialize(pss: PlayerStateSer, cards: dict[CardId, BaseCard]) -> 'PlayerState':
        return PlayerState(
            id      = pss.id,
            board   = Board.deserialize(pss.board, cards),
            hand    = Hand.deserialize(pss.hand),
            deck    = Deck.deserialize(pss.deck),
            discard = Deck.deserialize(pss.discard),
            money   = pss.money,
            items   = [Item.deserialize(itemser) for itemser in pss.items]
        )

@dataclass
class PlayerStateSer:
    id:                 str
    board:              dict[str, CardId | None]
    hand:               list[CardId]
    deck:               list[CardId]
    discard:            list[CardId]
    money:              float
    items:              list[ItemSer]

    @classmethod
    def from_dict(cls, d: dict) -> "PlayerStateSer":
        return cls(
            id=d["id"],
            board={k: (None if v is None else int(v)) for k, v in d["board"].items()},
            hand=[int(cid) for cid in d["hand"]],
            deck=[int(cid) for cid in d["deck"]],
            discard=[int(cid) for cid in d["discard"]],
            money=int(d["money"]),           # money is int in the DTO
            items=[ItemSer.from_dict(i) for i in d["items"]],
        )

# GameState.serialize stays as-is (modulo the variable name fix)
# GameState.deserialize gains the id-counter advance + Category conversion

@dataclass(frozen=True)
class GameView:
    me:              PlayerId
    players:         dict[PlayerId, PlayerView]
    cards:           dict[CardId, CardSer]
    active_ring:     dict[str, Any]
    active_category: str
    turn:            PlayerId
    n_actions_left:  int

    @staticmethod
    def to_view(gss: GameStateSer, viewer: PlayerId) -> "GameView":
        return GameView(
            me=viewer,
            players={pid: PlayerView.to_view(pss, viewer) for pid, pss in gss.players.items()},
            cards=gss.cards,
            active_ring=gss.active_ring,
            active_category=gss.active_category,
            turn=gss.turn,
            n_actions_left=gss.n_actions_left,
        )


@dataclass(frozen=True)
class PlayerView:
    board:              dict[str, CardId | None]
    hand_size:          int
    hand:               list[CardId] | None     # full cards only for me!
    deck_size:          int
    discard:            list[CardId]            # public
    money:              float
    items:              list[ItemSer]

    @staticmethod
    def to_view(pss: PlayerStateSer, viewer: PlayerId) -> PlayerView:
        is_me = viewer == pss.id # view full details only if I am the player in question
        return PlayerView(
            board       = pss.board,
            hand_size   = len(pss.hand),
            hand        = pss.hand if is_me else None,
            deck_size   = len(pss.deck),
            discard     = pss.discard,
            money       = pss.money,
            items       = pss.items
        )