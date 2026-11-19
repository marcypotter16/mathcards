import pyray as rl
from shaders.shaders import Shaders

from draw_debug import draw_debug
from entities.card.base import BaseCard, SpellCardSer
from mathematics.vector import Vector2
from Settings import COLOR_WHEN_UNPLAYABLE
from spell_db import SPELL_ACTIONS, SPELL_TYPST
from state_manager import StateManager
from utility import draw_fitted_texture


class SpellCard(BaseCard):
    """
    A spell card that triggers a game action when played.
    Visually distinct from Element cards (purple background, spell text).
    """
    DIMENSIONS = Vector2(150, 225)

    def __init__(
        self, 
        sm: StateManager, 
        spell: str, 
        card_id: int | None = None
    ) -> None:
        super().__init__(card_id)
        self.sm = sm
        self.spell = spell
        self.action = SPELL_ACTIONS[spell]
        self.formula = SPELL_TYPST[spell]
        
        # Spells usually aren't placed into the ring slots
        self.is_slottable = False 
        
        # --- Visual Config ---
        self.bg_color = rl.Color(80, 40, 120, 255)  # Deep magical purple
        self.border_thickness = 8
        self.border_color = rl.BLACK
        
        # Queue the formula rendering
        head = """
            #set page(width: auto, height: auto, margin: 4.0pt, fill: none)
            #set text(size: 12pt, fill: black)
        """
        self.ff = self.sm.tfr.queue_formula(f"${self.formula}$", 300, custom_header=head)
        self.tex: rl.Texture | None = None
        
        self.render_texture: rl.RenderTexture | None = None
        self.texture_is_dirty = True

    @property
    def is_ready(self) -> bool:
        self._ensure_render_texture()
        return self.tex is not None and self.back_tex is not None

    def _ensure_render_texture(self) -> None:
        if self.render_texture is None:
            self.render_texture = rl.load_render_texture(int(self.DIMENSIONS.x), int(self.DIMENSIONS.y))
            rl.set_texture_filter(self.render_texture.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)

    def update(self, dt: float) -> None:
        super().update(dt)
        
        # Check if the Typst formula has finished rendering in the background
        if self.tex is None:
            formula_ready = self.ff.done()
            draw_debug(
                "SpellCard.update formula poll",
                f"card={self.card_id}",
                f"ready={formula_ready}",
            )
            if formula_ready:
                res = self.ff.result()
                draw_debug(
                    "SpellCard.update formula result",
                    f"card={self.card_id}",
                    f"success={res.success}",
                    f"return_code={res.return_code}",
                    f"png_exists={res.png_path.is_file()}",
                )
                if res.success:
                    self.tex = rl.load_texture(str(res.png_path.resolve()))
                    rl.set_texture_filter(self.tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
                    self.texture_is_dirty = True
                    draw_debug(
                        "SpellCard.update GPU texture loaded",
                        f"card={self.card_id}",
                        f"texture_id={self.tex.id}",
                        f"size={self.tex.width}x{self.tex.height}",
                    )

    def bake_texture(self) -> None:
        self._ensure_render_texture()
        assert self.render_texture is not None
        
        rl.begin_texture_mode(self.render_texture)
        rl.clear_background(rl.BLANK)
        
        bt = self.border_thickness
        W, H = self.DIMENSIONS.x - bt, self.DIMENSIONS.y - bt
        header_h = 50 

        # 1. Draw Outer Border
        rl.draw_rectangle_rounded(rl.Rectangle(0, 0, W + bt, H + bt), 0.1, 0, self.border_color)

        x = y = bt / 2

        # 2. Draw Full Card Background
        rl.draw_rectangle_rounded(rl.Rectangle(x, y, W, H), 0.1, 4, self.bg_color if self.is_playable else COLOR_WHEN_UNPLAYABLE)

        # 3. Define Boxes
        header_box = rl.Rectangle(x, y, W, header_h)
        body_rect  = rl.Rectangle(x + 10, y + header_h, W - 20, H - header_h - 10)

        # Draw header divider line
        dimmed_bg = rl.Color(
            max(0, self.bg_color.r - 40), 
            max(0, self.bg_color.g - 40), 
            max(0, self.bg_color.b - 40), 
            255
        )
        rl.draw_line(10, int(header_box.y + header_box.height), int(W - 10), int(header_box.y + header_box.height), dimmed_bg)

        # 4. Draw Header Text
        label = self.spell
        font = self.sm.font
        text_size = rl.measure_text_ex(font, label, 20.0, 1.0)
        text_pos = rl.Vector2(
            header_box.x + (header_box.width - text_size.x) / 2, 
            header_box.y + (header_box.height - text_size.y) / 2
        )
        rl.draw_text_ex(font, label, text_pos, 20.0, 1.0, rl.Color(220, 200, 255, 255))

        # 5. Draw Main Formula
        if self.tex is not None:
            draw_fitted_texture(self.tex, body_rect)
        else:
            # Draw a placeholder while rendering
            text_size2 = rl.measure_text_ex(font, "...", 30.0, 1.0)
            text_pos2 = rl.Vector2(
                body_rect.x + (body_rect.width - text_size2.x) / 2,
                body_rect.y + (body_rect.height - text_size2.y) / 2
            )
            rl.draw_text_ex(font, "...", text_pos2, 30.0, 1.0, rl.WHITE)

        rl.end_texture_mode()
        self.texture_is_dirty = False

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        self._ensure_render_texture()
        assert self.render_texture is not None
        
        if self.texture_is_dirty:
            draw_debug(
                "SpellCard.render dirty texture",
                f"card={self.card_id}",
                f"logical_target={logical_texture}",
                f"card_target={self.render_texture}",
            )
            self.bake_texture()
            if logical_texture is not None:
                draw_debug("SpellCard.render restoring logical target", f"card={self.card_id}")
                rl.begin_texture_mode(logical_texture)
                draw_debug("SpellCard.render logical target restored", f"card={self.card_id}")

        Shaders.card_visuals.draw(self)

    def unload(self) -> None:
        """Clean up GPU resources."""
        if self.tex is not None:
            rl.unload_texture(self.tex)
            self.tex = None
        if self.render_texture is not None:
            rl.unload_render_texture(self.render_texture)
            self.render_texture = None

    ### SERIALIZATION ###
    def serialize(self) -> SpellCardSer:
        return SpellCardSer(
            id        = self.card_id,
            spell     = self.spell,
        )

    def apply(self, sd: SpellCardSer) -> None:
        # The spell identity is immutable for this card instance. 
        # If the incoming serialization doesn't match, something went wrong.
        if sd.spell != self.spell:
            raise ValueError(
                f"SpellCard.apply: spell identity mismatch {self.spell} -> {sd.spell}"
            )
        # No mutable state to update (the ID and type are fixed).

    @classmethod
    def from_ser(cls, cd: SpellCardSer, game: StateManager) -> SpellCard:
        if cd.spell not in SPELL_ACTIONS:
            raise ValueError(f"Unknown spell type '{cd.spell}'")
        return cls(game, cd.spell, card_id=cd.id)
