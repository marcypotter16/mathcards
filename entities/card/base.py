from abc import ABC
from enum import StrEnum, auto
import itertools
from typing import Any, Callable, Literal

from Tweener import Tween, TweenManager, TweenParams
from entities.base import Entity
from mathematics.vector import Vector2
import pyray as rl
from dataclasses import dataclass

type CardId = int

class CardType(StrEnum):
    ELEMENT                 = auto() # e.g., a 4
    OPERATOR                = auto() # e.g., a "+" or "Invert"
    
@dataclass(frozen=True)
class ElementCardSer:
    id:                     int
    base_element_ser:       dict[str, Any]
    current_element_ser:    dict[str, Any]
    ring_ser:               dict[str, Any]
    card_type:              Literal[CardType.ELEMENT] = CardType.ELEMENT  

@dataclass(frozen=True)
class OperatorCardSer:
    id:                     int
    operator:               str
    arity:                  int | Literal["n-ary"]
    card_type:              Literal[CardType.OPERATOR] = CardType.OPERATOR

type CardSer                = ElementCardSer | OperatorCardSer


class BaseCard(Entity, ABC):
    """Just the base abstract class for cards. Not to be instantiated."""
    _counter = itertools.count(1)

    @classmethod
    def _next_id(cls) -> int:
        return next(BaseCard._counter)

    @classmethod
    def _set_id_counter(cls, new_counter: int) -> None:
        BaseCard._counter = itertools.count(new_counter)

    DIMENSIONS = Vector2(150, 225)

    def __init__(self, card_id: int | None = None) -> None:
        super().__init__()
        self.card_id                                = card_id if card_id is not None else self._next_id()
        self.z_index:               int
        self.state:                 CardState
        self.center:                Vector2         = Vector2(0, 0)
        self.center_before_drag:    Vector2         = Vector2(0, 0)
        self.rotation:              float           = 0.0
        self.scale:                 float           = 1.0
        self.rot_when_hov:          float           = -9.0
        self.scale_when_hov:        float           = 1.1

        self.tm:                    TweenManager    = TweenManager()
    
    def bake_texture(self):
        return NotImplemented
    
    def get_rect(self) -> rl.Rectangle:
        return rl.Rectangle(self.center.x - self.DIMENSIONS.x * .5, self.center.y - self.DIMENSIONS.y * .5, self.DIMENSIONS.x, self.DIMENSIONS.y)
    
    def get_center(self) -> Vector2:
        return self.center
    
    def get_center_after_hover(self) -> Vector2:
        return self.center + Vector2(0, -1) * .1 * self.DIMENSIONS.y
    
    def place_card(self, new_pos: Vector2):
        """This actually resets the card's before-hover and before-drag centers to the new position"""
        self.center = self.center_rest = self.center_before_drag = new_pos
    
    def tween_center(self, new_pos: Vector2, dur=0.2, easing_type='ease-in-out-cubic', callback: Callable | None = None):
        self.tm.add_tween(Tween(TweenParams(self, "center", new_pos, dur=dur, easing_type=easing_type, callback=callback)), kill_existing=True) # type: ignore
    
    def tween_rotation(self, new_rot: float, dur=0.2):
        self.tm.add_tween(Tween(TweenParams(self, "rotation", new_rot, dur=dur, easing_type='ease-out-cubic')), kill_existing=True)
    
    def tween_scale(self, new_scale: float, dur=0.2):
        self.tm.add_tween(Tween(TweenParams(self, "scale", new_scale, dur=dur, easing_type='ease-out-cubic')), kill_existing=True)
    
    def snap_back(self):
        self.tween_center(self.center_before_drag, dur=0.8, callback=lambda: setattr(self, '_is_snapping_back', False))
        if self.scale != 1.0:
            self.tween_scale(1.0)
    
    def update(self, dt):
        self.tm.update(dt)
    
    def render(self, logical_texture: rl.RenderTexture | None):
        return NotImplemented
    
    def unload(self):
        return NotImplemented

    def serialize(self) -> CardSer: ...
    def apply(self, d: BaseCard): ...
    @classmethod
    def deserialize(cls, d): ...

@dataclass
class CardState:
    is_dragged:             bool = False
    is_hovered:             bool = False
    started_dragging:       bool = False
    started_hovering:       bool = False
    ended_dragging:         bool = False
    ended_hovering:         bool = False
    _last_frame_dragged:    bool = False
    _last_frame_hovered:    bool = False

    def clear_frame_triggers(self):
        """Only clear event triggers at the start of a frame. 
        Persistent states like 'is_dragged' and 'is_hovered' must NOT be wiped here."""
        self.started_dragging   = False
        self.started_hovering   = False
        self.ended_dragging     = False
        self.ended_hovering     = False

    def update_last_frame_vars(self):
        self._last_frame_dragged = self.is_dragged
        self._last_frame_hovered = self.is_hovered
