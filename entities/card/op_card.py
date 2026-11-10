from enum import StrEnum
from typing import Literal
from Settings import COLOR_OP
from entities.card.base import BaseCard, OperatorCardSer
from state_manager import StateManager
from mathematics.vector import Vector2
from tfr import TypstFormulaRenderer

import pyray as rl


class OperatorType(StrEnum):
    ADD                     = "+"
    INVERT                  = "^-1"
    MUL                     = "*"
    SUB                     = "-"

    
# color_map = {
#     OperatorType.ADD:    COLOR_OP_ADD,
#     OperatorType.SUB:    COLOR_OP_SUB,
#     OperatorType.MUL:    COLOR_OP_MUL,
#     OperatorType.INVERT: COLOR_OP_INVERT,
# }

def color_to_hex(c: rl.Color) -> str:
    """Safely converts a raylib color to a hex string, handling tuple returns."""
    if isinstance(c, tuple):
        r, g, b = c[0], c[1], c[2]
    else:
        r, g, b = c.r, c.g, c.b
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def get_contrast_color(bg: rl.Color) -> rl.Color:
    if isinstance(bg, tuple):
        r, g, b = bg[0], bg[1], bg[2]
    else:
        r, g, b = bg.r, bg.g, bg.b
    
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return rl.BLACK if luminance > 0.5 else rl.WHITE

class OpCard(BaseCard):
    """An operator card, like "+", "-", and so on."""

    OPT2TYPST:  dict[OperatorType, str] = {
        OperatorType.ADD: "$+$",
        OperatorType.SUB: "$-$",
        OperatorType.MUL: "$dot.c$",
        OperatorType.INVERT: "$square^(-1)$"
    }
    ARITY:      dict[OperatorType, Literal['n-ary'] | int] = {
        OperatorType.ADD: 'n-ary',
        OperatorType.SUB: 'n-ary',
        OperatorType.MUL: 'n-ary',
        OperatorType.INVERT: 1
    }
    
    # --- Vertical Layout to match EORCard ---
    DIMENSIONS = Vector2(150, 225)

    def __init__(self, game: StateManager, type: OperatorType, card_id: int | None = None) -> None:
        super().__init__(card_id)
        self.op_type:       OperatorType        = type
        self.tfr                                = game.tfr
        ppi                                     = 180

        self.is_slottable = False
        
        self.bg_color = COLOR_OP
        self.border_thickness = 8
        self.border_color = rl.BLACK
        self.text_color = get_contrast_color(self.bg_color)

        # We use the text color here so the math formula matches the card theme
        hex_color = color_to_hex(self.text_color)
        
        crop_header = (
            "#set page(width: auto, height: auto, margin: 10pt, fill: none)\n"
            f"#set text(size: 24pt, fill: rgb(\"{hex_color}\"), stroke: 0.6pt)\n"
            "#set math.frac(style: \"vertical\")\n"
        )
        
        self.ff = self.tfr.queue_formula(self.OPT2TYPST[type], ppi, custom_header=crop_header)
        self.tex: rl.Texture | None = None

        # Inner state
        self.render_texture: rl.RenderTexture | None = None
        self.texture_is_dirty = True
        self.game = game

    def _ensure_render_texture(self) -> None:
        if self.render_texture is None:
            self.render_texture = rl.load_render_texture(int(self.DIMENSIONS.x), int(self.DIMENSIONS.y))
            rl.set_texture_filter(self.render_texture.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)

    def update(self, dt):
        super().update(dt)

        if self.tex is None and self.ff.done():
            res = self.ff.result()
            path = str(res.png_path.resolve())
            self.tex = rl.load_texture(path)
            rl.set_texture_filter(self.tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
            self.texture_is_dirty = True

    def bake_texture(self):
        self._ensure_render_texture()
        assert self.render_texture is not None
        
        rl.begin_texture_mode(self.render_texture)
        rl.clear_background(rl.BLANK)

        bt = self.border_thickness
        # Render texture is WxH. We inset the background by bt/2 so the border is visible.
        W, H = self.DIMENSIONS.x - bt, self.DIMENSIONS.y - bt
        offset = bt / 2

        # 1. Draw Outer Border (Full size)
        rl.draw_rectangle_rounded(rl.Rectangle(0, 0, W + bt, H + bt), 0.1, 4, self.border_color)

        # 2. Draw Card Background (Inset by bt/2)
        rl.draw_rectangle_rounded(rl.Rectangle(offset, offset, W, H), 0.1, 4, self.bg_color)

        # 3. Draw Top-Left Label
        label_map = {
            "ADD": "addition",
            "SUB": "subtraction",
            "MUL": "multiplication",
            "INVERT": "inversion"
        }
        op_name = label_map.get(self.op_type.name, self.op_type.name.lower())
        
        # Offset the text by the border + padding
        rl.draw_text_ex(self.game.font, op_name, (offset + 10, offset + 10), 20, 1.0, self.text_color)

        # 4. Draw Central Math Operator
        if self.tex is not None:
            scale = 1.5 
            dest_w = int(self.tex.width * scale)
            dest_h = int(self.tex.height * scale)
            
            # Calculate center based on the inset W and H
            dest_x = int(offset + (W - dest_w) / 2)
            dest_y = int(offset + (H - dest_h) / 2)
            
            rl.draw_texture_pro(
                self.tex,
                rl.Rectangle(0, 0, self.tex.width, self.tex.height),
                rl.Rectangle(dest_x, dest_y, dest_w, dest_h),
                rl.Vector2(0, 0),
                0,
                rl.WHITE
            )

        rl.end_texture_mode()
        self.texture_is_dirty = False

    def render(self, logical_texture: rl.RenderTexture | None = None):
        """Draws the pre-baked card texture to the screen."""
        self._ensure_render_texture()
        assert self.render_texture is not None
        
        if self.texture_is_dirty:
            self.bake_texture()
            if logical_texture is not None:
                rl.begin_texture_mode(logical_texture)

        rl.draw_texture_pro(
            self.render_texture.texture, 
            rl.Rectangle(0, 0, self.DIMENSIONS.x, -self.DIMENSIONS.y), 
            rl.Rectangle(
                int(self.center.x), 
                int(self.center.y), 
                int(self.DIMENSIONS.x * self.scale), 
                int(self.DIMENSIONS.y * self.scale)
            ),
            rl.Vector2(int(self.DIMENSIONS.x * self.scale / 2), int(self.DIMENSIONS.y * self.scale / 2)), 
            self.rotation,
            rl.WHITE
        )

    ### SERIALIZATION ###
    def serialize(self):
        return OperatorCardSer(
            self.card_id,
            self.op_type.name,
            self.ARITY[self.op_type]
        )

    def apply(self, sd: OperatorCardSer) -> None:
        if sd.operator != self.op_type:
            raise ValueError(
                f"OpCard.apply: op_type is identity, cannot change {self.op_type} -> {sd.operator}"
            )

    @classmethod
    def from_ser(cls, sd: OperatorCardSer, g: StateManager) -> "OpCard":
        op = OperatorType[sd.operator] if isinstance(sd.operator, str) else sd.operator
        return cls(g, op, card_id=sd.id)