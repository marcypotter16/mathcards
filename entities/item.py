from entities.base import Entity
from entities.game_manager.dataclasses import ItemSer


class Item(Entity):
    def __init__(self) -> None:
        super().__init__()

    def serialize(self) -> ItemSer:
        return NotImplemented

    @classmethod
    def deserialize(cls, data: ItemSer) -> Item:
        return NotImplemented