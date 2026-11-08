from dataclasses import dataclass
from typing import Any

from entities.base import Entity


class Item(Entity):
    def __init__(self) -> None:
        super().__init__()

    def serialize(self) -> ItemSer:
        return NotImplemented

    @classmethod
    def deserialize(cls, data: ItemSer) -> Item:
        return NotImplemented

@dataclass(frozen=True)
class ItemSer:
    id:         str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ItemSer:
        return cls(
            id = d["id"]
        )
