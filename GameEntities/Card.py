from enum import StrEnum
from pathlib import Path
import random
from typing import Callable, Literal

from GameEntities.Entity import Entity
import pyray as rl
from dataclasses import dataclass

from Vector import Vector2
from Settings import FONT_PATH
from Tweener import Tween, TweenManager, TweenParams

class Suit(StrEnum):
    SPADES = "S"
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    NONE = " "

BASE_SUIT_PATH = Path("assets", "suits")
CLASSIC_SUITS_PATH = Path(BASE_SUIT_PATH, "classic")
SUITS_SVG_PATHS = {
    Suit.SPADES: Path(CLASSIC_SUITS_PATH, "spade.png"),
    Suit.HEARTS: Path(CLASSIC_SUITS_PATH, "heart.png"),
    Suit.DIAMONDS: Path(CLASSIC_SUITS_PATH, "diamond.png"),
    Suit.CLUBS: Path(CLASSIC_SUITS_PATH, "club.png")
}
VALUES_TO_RANKS = {
    1: "A",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "J",
    9: "Q",
    10: "K",
}

CACHED_SUITS_TEXTURES: dict[Suit, rl.Texture] = {}
def init_cards():    # call this after opening a gl context (initializing raylib) 
    for suit in Suit:
        if suit is not Suit.NONE:
            CACHED_SUITS_TEXTURES[suit] = rl.load_texture(str(SUITS_SVG_PATHS[suit].resolve()))

@dataclass
class CardData:
    rank: int
    suit: Suit
    @property
    def color(self) -> Literal['black', 'red']:
        return 'black' if self.suit in (Suit.SPADES, Suit.CLUBS) else 'red'

    def __repr__(self) -> str:
        return f"({VALUES_TO_RANKS[self.rank]}{self.suit.value})"

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

class Card(Entity):
    def __init__(self, rank: int = 0, suit: Suit = Suit.NONE, card_data: CardData | None = None, _dont_initialize_render_texture=False) -> None:
        if card_data is not None:
            self.card_data = card_data
        else:
            self.card_data = CardData(rank, suit)
        print(self.card_data.suit)
        if self.card_data.suit != Suit.NONE:
            self.set_data(self.card_data)
        self.width, self.height                         = 150, 225
        self.center:                Vector2             = Vector2(100, 200)
        self.center_rest:           Vector2             = Vector2(100, 200)
        self.center_before_drag:    Vector2             = Vector2(100, 200)
        self.rotation:              float               = 0.0
        self.scale:                 float               = 1.0
        self.rot_when_hovered:      float               = -9.0
        self.scale_when_hovered:    float               = 1.1
        self.dimensions:            Vector2             = Vector2(self.width, self.height)
        if not _dont_initialize_render_texture:
            self.render_texture:        rl.RenderTexture    = rl.load_render_texture(self.width, self.height)
            rl.set_texture_filter(
                self.render_texture.texture, 
                rl.TextureFilter.TEXTURE_FILTER_TRILINEAR
            )
        self.texture_is_dirty:      bool                = True
        self.suit_size:             int                 = 60
        self.font_size:             int                 = 32
        self.bg_color:              rl.Color            = rl.RAYWHITE
        self.border_color:          rl.Color            = rl.BLACK
        self.border_thickness:      int                 = 8
        self.font:                  rl.Font             = rl.load_font(FONT_PATH)
        self.rank_inset:            Vector2             = Vector2(8, 5) + Vector2(self.border_thickness, self.border_thickness)

        self.z_index:               int

        self.state:                 CardState           = CardState()
        self._timer:                float               = 0.0
        self._is_snapping_back:     bool                = False

        self.tm:                    TweenManager        = TweenManager()


    def set_data(self, cd: CardData):
        self.suit_tex = CACHED_SUITS_TEXTURES.get(cd.suit)
        self.card_data = cd
        self.texture_is_dirty = True

    def bake_texture(self):
        """Renders the card's internal graphics onto its own texture."""
        rl.begin_texture_mode(self.render_texture)
        rl.clear_background(rl.BLANK)
        bt = self.border_thickness
        # outline
        rl.draw_rectangle_rounded(
            rl.Rectangle( 0, 0, self.width, self.height ), 
            .1, 
            0, 
            self.border_color)
        rl.draw_rectangle_rounded(
            rl.Rectangle( bt * .5, bt * .5, self.width - bt, self.height - bt ), 
            .1, 
            4, 
            self.bg_color)
        # DRAW SUIT
        if self.suit_tex is not None:
            if self.suit_tex.id > 0:
                texture = self.suit_tex
                source = rl.Rectangle(0, 0, texture.width, texture.height)
                destination = rl.Rectangle(
                    self.width * .5 - self.suit_size * .5,
                    self.height * .5 - self.suit_size * .5,
                    self.suit_size,
                    self.suit_size,
                )
                destination_topright = rl.Rectangle(
                    self.width - self.border_thickness * .5 - 5 - self.font_size,
                    self.border_thickness * .5 + 10,
                    self.font_size,
                    self.font_size
                )
                destination_botleft = rl.Rectangle(
                    self.border_thickness * .5 + 5 + self.font_size * .5,
                    self.height - self.border_thickness * .5 - 10 - self.font_size * .5,
                    self.font_size,
                    self.font_size
                )
                x, y, w, h = destination_botleft.x, destination_botleft.y, destination_botleft.width, destination_botleft.height
                botleft_rot_origin = rl.Vector2(w * .5, h * .5)
                rl.draw_texture_pro(texture, source, destination, rl.vector2_zero(), 0, rl.WHITE)
                rl.draw_texture_pro(texture, source, destination_topright, rl.vector2_zero(), 0, rl.WHITE)
                rl.draw_texture_pro(texture, source, destination_botleft, botleft_rot_origin, 180, rl.WHITE)
        # DRAW RANKS
        if self.font is not None:
            text_color = rl.BLACK if self.card_data.color == 'black' else rl.RED
            rl.draw_text_ex(self.font, VALUES_TO_RANKS[self.card_data.rank], self.rank_inset.raylib_ref, self.font_size, 1, text_color)
            # rl.draw_text(VALUES_TO_RANKS[self.card_data.rank], 5, 5, 24, text_color)
            inverted_rank_pos = (self.dimensions - self.rank_inset).raylib_ref
            rl.draw_text_pro(
                self.font,
                # rl.get_font_default(), 
                VALUES_TO_RANKS[self.card_data.rank], 
                inverted_rank_pos, 
                rl.vector2_zero(), 
                180,                # rotation 
                self.font_size,     # font size
                1,                  # spacing
                text_color)
        rl.end_texture_mode()
        self.texture_is_dirty = False

    def get_rect(self):
        return rl.Rectangle(self.center._x - self.dimensions._x * .5, self.center._y - self.dimensions._y * .5, self.width, self.height)

    def get_center(self) -> Vector2:
        return self.center

    def get_center_after_hover(self) -> Vector2:
        return self.center + Vector2(0, -1) * .1 * self.height

    def place_card(self, new_pos):
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

    def _be_a_lil_silly(self):
        if self._timer >= 1.0:
            self._timer = 0.0
            rank = random.randint(1, 10)
            suit = random.choice([s for s in Suit if s is not Suit.NONE])
            self.set_data(CardData(rank, suit))

    def __repr__(self) -> str:
        return self.card_data.__repr__()

    def update(self, dt):
        if self._is_snapping_back:
            self.tm.update(dt)
            return
        mouse = Vector2.from_raylib(rl.get_mouse_position())

        # 5. Process continuous physics/movement based on states
        if self.state.is_dragged:
            self.center = Vector2.from_raylib(rl.vector2_lerp(self.center.raylib_ref, mouse.raylib_ref, 22.0 * dt))

        # 6. Process Visual Tweens from triggers
        if self.state.started_hovering:
            self.tween_scale(self.scale_when_hovered)
            self.tween_center(self.get_center_after_hover())
        elif self.state.ended_hovering:
            self.tween_center(self.center_rest)
            self.tween_scale(1.0)

        if self.state.started_dragging:
            self.center_before_drag = Vector2(self.center_rest.x, self.center_rest.y)
            self.tween_rotation(self.rot_when_hovered)
        elif self.state.ended_dragging:
            self._is_snapping_back = True
            self.snap_back()
            self.tween_rotation(0.0)
            
        # 7. Engine & Data updates
        self.tm.update(dt)

        self._timer += dt

        # self._be_a_lil_silly()
        
    def render(self, logical_texture: rl.RenderTexture):
        # If card data changed, re-bake the texture before drawing it
        if self.texture_is_dirty:
            self.bake_texture()
            # basically we have to re-enter logical_texture mode since end_texture_mode 
            # exits every active texture mode
            rl.begin_texture_mode(logical_texture)
        rl.draw_texture_pro(
            self.render_texture.texture, 
            rl.Rectangle( 0, 0, self.width, -self.height ), # minus sign because opengl inverts y axis
            rl.Rectangle( self.center._x, self.center._y, self.width * self.scale, self.height * self.scale ),
            rl.Vector2((self.width * self.scale) / 2, (self.height * self.scale) / 2),
            self.rotation,
            rl.WHITE)

    def unload(self):
        rl.unload_render_texture(self.render_texture)