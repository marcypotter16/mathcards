from enum import StrEnum, Enum, auto
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from entities.card.base import CardId, CardSer, BaseCard
from entities.card.factory import card_from_ser, card_ser_from_dict
from entities.item import ItemSer
from entities.player import PlayerId, PlayerState, PlayerStateSer, PlayerView
from state_manager import StateManager

from entities.hand import Hand
from entities.board import Board
from entities.deck import Deck
from mathematics.base import Category, CommUnitRing

if TYPE_CHECKING:
    from entities.item import Item

from mathematics.serialization import deserialize_ring, serialize_ring

from dataclasses import dataclass

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
    def deserialize(gss: GameStateSer, game: StateManager) -> 'GameState':
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

        boards = gss.boards

        return GameState(
            players         = players,
            boards          = {pid: pstate.board for pid, pstate in players.items()},
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
