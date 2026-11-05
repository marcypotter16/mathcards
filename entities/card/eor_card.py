from entities.card.base import BaseCard
from mathematics.base import CommUnitRing
from mathematics.serialization import deserialize_element, deserialize_ring, serialize_element, serialize_ring
from mathematics.vector import Vector2
from entities.card.base import CardSer, CardType, ElementCardSer
from tfr import TypstFormulaRenderer

import pyray as rl

def get_crop_header(base_font_pt) -> str:
    return (
            "#set page(width: auto, height: auto, margin: 10pt, fill: none)\n"
            f"#set text(size: {base_font_pt}pt, fill: black, stroke: 0.6pt)\n"
            "#set math.frac(style: \"vertical\")\n"
        )

class EORCard[T](BaseCard):
    """EOR = Element Of Ring: a card like "x" in ZZ[x]"""

    DIMENSIONS = Vector2(225, 150)

    def __init__(self, ring: CommUnitRing[T], element: T, tfr: TypstFormulaRenderer, card_id: int | None = None) -> None:
        super().__init__(card_id)
        self.ring = ring
        self.base_value = self.current_value = element
        self.tfr = tfr

        base_font_pt = 24.0
        ppi = 100

        crop_header = get_crop_header(base_font_pt)

        # --- Ring ---
        ring_str = getattr(ring, "typst_str", str(ring))
        self.ring_ff = self.tfr.queue_formula(f"${ring_str}$", ppi=ppi, custom_header=crop_header)
        self.ring_tex: rl.Texture | None = None

        # --- Element ---
        str_el = getattr(element, "typst_str", str(element))
        self.el_ff = self.tfr.queue_formula(f"${str_el}$", ppi=ppi, custom_header=crop_header)
        self.el_tex: rl.Texture | None = None

        # --- Visual Config ---
        self.border_thickness = 8
        self.border_color = rl.BLACK
        self.bg_color = rl.RAYWHITE
        self.el_bg_color = rl.RAYWHITE
        self.ring_bg_color = rl.GRAY
        
        # Size for the formula in the center
        self.formula_size = 100 

        # --- Physics/State (from BaseCard) ---
        self.center = Vector2(100, 200)
        self.center_rest = Vector2(100, 200)
        self.center_before_drag = Vector2(100, 200)
        self.rotation = 0.0
        self.scale = 1.0

        self.render_texture: rl.RenderTexture | None = None
        self.texture_is_dirty = True

    def _ensure_render_texture(self) -> None:
        if self.render_texture is None:
            self.render_texture = rl.load_render_texture(int(self.DIMENSIONS.x), int(self.DIMENSIONS.y))
            rl.set_texture_filter(self.render_texture.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)

    def update(self, dt):
        super().update(dt)
        
        if self.ring_tex is None and self.ring_ff.done():
            self.ring_tex = rl.load_texture(str(self.ring_ff.result().png_path.resolve()))
            rl.set_texture_filter(self.ring_tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
            self.texture_is_dirty = True
            
        if self.el_tex is None and self.el_ff.done():
            self.el_tex = rl.load_texture(str(self.el_ff.result().png_path.resolve()))
            rl.set_texture_filter(self.el_tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
            self.texture_is_dirty = True

    def _draw_fitted_texture(self, tex: rl.Texture, bounding_box: rl.Rectangle):
        """Draws a texture centered in a bounding box, scaling down only if it overflows."""
        if tex is None or tex.id <= 0:
            return

        # 85% of the bounding box gives natural padding
        max_w = bounding_box.width * 0.85
        max_h = bounding_box.height * 0.85
        
        scale_w = max_w / tex.width
        scale_h = max_h / tex.height
        
        # We use min(1.0, ...) so we NEVER scale up a small texture (keeps it 1:1 crisp)
        fit_scale = min(1.0, scale_w, scale_h)
        
        draw_w = int(tex.width * fit_scale)
        draw_h = int(tex.height * fit_scale)
        
        center_x = bounding_box.x + (bounding_box.width * 0.5)
        center_y = bounding_box.y + (bounding_box.height * 0.5)
        
        dest_x = int(center_x - (draw_w * 0.5))
        dest_y = int(center_y - (draw_h * 0.5))
        
        rl.draw_texture_pro(
            tex,
            rl.Rectangle(0, 0, tex.width, tex.height),
            rl.Rectangle(dest_x, dest_y, draw_w, draw_h),
            rl.Vector2(0, 0), 
            0, 
            rl.WHITE
        )

    def bake_texture(self):
        self._ensure_render_texture()
        assert self.render_texture is not None
        rl.begin_texture_mode(self.render_texture)
        rl.clear_background(rl.BLANK)
        
        bt = self.border_thickness
        W, H = self.DIMENSIONS.x, self.DIMENSIONS.y
        header_h = 60 

        # 1. Draw Outer Border
        rl.draw_rectangle_rounded(rl.Rectangle(0, 0, W + bt, H + bt), 0.1, 0, self.border_color)

        # 2. Draw Ring Background (Header)
        # We need to clip this to the top rounded corners, so we draw a rounded rect
        # and then draw a flat rect over the bottom half of it to square it off.
        rl.draw_rectangle_rounded(rl.Rectangle(0, 0, W, H), 0.1, 4, self.ring_bg_color)
        # rl.draw_rectangle_rounded(rl.Rectangle(0, header_h * 0.5, W, header_h * 0.5), 0.1, 0, self.ring_bg_color)

        # 3. Draw Element Background (Body)
        body_margin = 10
        body_y = header_h + 5
        body_w = W - body_margin * 2
        body_h = H - body_y - body_margin
        body_rect = rl.Rectangle(body_margin, body_y, body_w, body_h)
        
        rl.draw_rectangle_rounded(body_rect, 0.1, 4, self.el_bg_color)


        # 5. Draw Separator Line
        # rl.draw_line(int(0), int(header_h), int(W), int(header_h), self.border_color)

        # 6. Draw Ring Formula
        if self.ring_tex is not None:
            header_box = rl.Rectangle(0, 0, W, header_h)
            self._draw_fitted_texture(self.ring_tex, header_box)

        # 7. Draw Element Formula
        if self.el_tex is not None:
            self._draw_fitted_texture(self.el_tex, body_rect)

        # 8. Draw Inner Box Border
        rl.draw_rectangle_rounded_lines(body_rect, 0.1, 0, self.border_color)

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

        # Draw the composed card texture using integer coordinates for sharpness
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
    def serialize(self) -> ElementCardSer:
        return ElementCardSer(
            id                  = self.card_id,
            base_element_ser    = serialize_element(self.base_value),
            current_element_ser = serialize_element(self.current_value),  # or self.current_element
            ring_ser            = serialize_ring(self.ring),
        )

    def apply(self, sd: ElementCardSer) -> None:
        if sd.ring_ser is None:
            raise ValueError("EORCard.apply: missing ring_ser")

        new_ring = deserialize_ring(sd.ring_ser)
        # element must be interpreted *in the new ring*, so deserialize after the ring
        new_current = (
            deserialize_element(sd.current_element_ser, new_ring)
            if sd.current_element_ser is not None
            else None
        )

        ring_changed   = (new_ring != self.ring)   # or serialize_ring(new_ring) != serialize_ring(self.ring)
        value_changed  = (new_current != self.current_value)

        self.ring = new_ring
        if new_current is not None:
            self.current_value = new_current
        # base_value is identity-ish; only refresh if you want the card to reflect it
        if sd.base_element_ser is not None:
            self.base_value = deserialize_element(sd.base_element_ser, new_ring)

        if ring_changed or value_changed:
            self._requeue_formulas()

    @classmethod
    def from_ser(cls, cd: ElementCardSer, tfr: TypstFormulaRenderer) -> "EORCard":
        if cd.ring_ser is None or cd.base_element_ser is None:
            raise ValueError("EORCard.from_ser: missing ring_tag / base_value")
        ring    = deserialize_ring(cd.ring_ser)
        element = deserialize_element(cd.base_element_ser, ring)
        card    = cls(ring, element, tfr, card_id=cd.id)
        curr    = deserialize_element(cd.current_element_ser, ring)
        if card.current_value != curr:
            card._requeue_formulas()
        card.current_value = curr
        return card
        

    def _requeue_formulas(self) -> None:
        # Same body as the two queue_formula calls in __init__, factored out.
        crop_header = get_crop_header(24)
        ring_str = getattr(self.ring, "typst_str", str(self.ring))
        self.ring_ff = self.tfr.queue_formula(f"${ring_str}$", ppi=100, custom_header=crop_header)
        self.ring_tex = None
        el_str = getattr(self.current_value, "typst_str", str(self.current_value))
        self.el_ff = self.tfr.queue_formula(f"${el_str}$", ppi=100, custom_header=crop_header)
        self.el_tex = None
        self.texture_is_dirty = True