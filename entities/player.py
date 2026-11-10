

from dataclasses import dataclass

from entities.board import Board
from entities.card.base import BaseCard, CardId
from entities.deck import Deck
from entities.discard_pile import DiscardPile
from entities.game_manager.dataclasses import ItemSer
from entities.hand import Hand
from entities.item import Item


type PlayerId = str

@dataclass
class PlayerState:
    id:                 PlayerId
    board:              Board
    hand:               Hand      # private
    deck:               Deck
    discard:            DiscardPile
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
            board   = Board.deserialize(pss.board),
            hand    = Hand.deserialize(pss.hand),
            deck    = Deck.deserialize(pss.deck),
            discard = DiscardPile.deserialize(pss.discard),
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
    items:              list[ItemSer
                             ]

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

@dataclass(frozen=True)
class PlayerView:
    viewer:             PlayerId
    board:              dict[str, CardId | None]
    hand_size:          int
    hand:               list[CardId] | None     # full cards only for me!
    deck_size:          int
    discard:            DiscardPile             # public
    money:              float
    items:              list[ItemSer]

    @staticmethod
    def to_view(pss: PlayerStateSer, viewer: PlayerId) -> PlayerView:
        is_me = viewer == pss.id # view full details only if I am the player in question
        return PlayerView(
            viewer      = pss.id,
            board       = pss.board,
            hand_size   = len(pss.hand),
            hand        = pss.hand if is_me else None,
            deck_size   = len(pss.deck),
            discard     = DiscardPile.deserialize(pss.discard),
            money       = pss.money,
            items       = pss.items
        )