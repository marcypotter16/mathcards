from enum import StrEnum
from typing import Literal

from entities.card.base import BaseCard, OperatorCardSer
from mathematics.vector import Vector2
from tfr import TypstFormulaRenderer

import pyray as rl

class OperatorType(StrEnum):
    ADD                     = "+"
    INVERT                  = "^-1"
    MUL                     = "*"
    SUB                     = "-"

class OpCard(BaseCard):
    """An operator card, like "+", "-", and so on."""

    OPT2TYPST:  dict[OperatorType, str] = {
        OperatorType.ADD: "$a + b$",
        OperatorType.SUB: "$a - b$",
        OperatorType.MUL: "$a dot.c b$",
        OperatorType.INVERT: "$a^(-1)$"
    }
    ARITY:      dict[OperatorType, Literal['n-ary'] | int] = {
        OperatorType.ADD: 'n-ary',
        OperatorType.SUB: 'n-ary',
        OperatorType.MUL: 'n-ary',
        OperatorType.INVERT: 1
    }
    DIMENSIONS = Vector2(225, 150)

    def __init__(self, type: OperatorType, tfr: TypstFormulaRenderer, card_id: int | None = None) -> None:
        super().__init__(card_id)
        self.op_type:       OperatorType        = type
        self.tfr                                = tfr
        ppi                                     = 200
        crop_header = (
            "#set page(width: auto, height: auto, margin: 10pt, fill: none)\n"
            f"#set text(size: {24}pt, fill: black, stroke: 0.6pt)\n"
            "#set math.frac(style: \"vertical\")\n"
        )
        self.ff                                 = self.tfr.queue_formula(self.OPT2TYPST[type], ppi, custom_header=crop_header)
        self.tex:           rl.Texture | None   = None

        self.bg_color:      rl.Color            = rl.LIME


    def update(self, dt):
        super().update(dt)

        if self.tex is None and self.ff.done():
            res = self.ff.result()
            path = str(res.png_path.resolve())
            self.tex = rl.load_texture(path)

    def render(self, logical_texture: rl.RenderTexture | None = None):
        """Draws the pre-baked card texture to the screen."""
        rl.draw_rectangle_rounded(self.get_rect(), 0.1, 0, self.bg_color)
        if self.tex is not None:
            topleft = self.center - Vector2(int(self.tex.width / 2), int(self.tex.height / 2))
            rl.draw_texture_v(self.tex, topleft.raylib_ref, rl.BLACK)


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
    # card_id is also identity; don't reassign it here either (same rule as EORCard)

    @classmethod
    def from_ser(cls, sd: OperatorCardSer, tfr: TypstFormulaRenderer) -> "OpCard":
        op = OperatorType[sd.operator] if isinstance(sd.operator, str) else sd.operator
        return cls(op, tfr, card_id=sd.id)