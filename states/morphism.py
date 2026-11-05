# states/morphism.py
from concurrent.futures import Future
from typing import TYPE_CHECKING, Any, Callable

import pyray as rl

import Settings
from entities.ring_el_widget import RingElementConstructor
from mathematics.base import CommUnitRing
from mathematics.vector import Vector2
from states.base import State
from tfr import FormulaResult, TypstFormulaRenderer

if TYPE_CHECKING:
    from game import Game


class MorphismConstructorState(State):
    """
    Dedicated game state for defining a ring homomorphism phi: Domain -> Codomain.
    Displays domain and codomain formulas, lists generators with interactive target sockets,
    and opens a RingElementConstructor widget to input images for each generator.
    Uses custom TTF font rendering with anti-aliasing.
    """

    def __init__(
        self,
        game: "Game",
        domain: CommUnitRing,
        codomain: CommUnitRing,
        on_complete: Callable[[dict[Any, Any]], None] | None = None,
    ) -> None:
        super().__init__(game)
        self.domain = domain
        self.codomain = codomain
        self.on_complete = on_complete

        self.lww: int = Settings.WINDOW.get("L_WIDTH", 1920)
        self.lwh: int = Settings.WINDOW.get("L_HEIGHT", 1080)
        self.tfr: TypstFormulaRenderer = game.tfr
        self.font: rl.Font = getattr(game, "font", rl.get_font_default())

        # Main workspace card dimensions
        card_margin_x = 80
        card_margin_y = 60
        self.card_rect = rl.Rectangle(
            card_margin_x,
            card_margin_y,
            self.lww - 2 * card_margin_x,
            self.lwh - 2 * card_margin_y,
        )
        self.center_of_morphism = Vector2(int(self.lww / 2), int(self.lwh / 2))

        # Stable, sorted list of domain generators
        self.generators: list[Any] = self._get_sorted_generators()

        # Assigned images: generator_index -> codomain_value
        self.assigned_images: dict[int, Any] = {}

        # Typst rendering state
        self.morph_fut: Future[FormulaResult] | None = None
        self.morph_res: FormulaResult | None = None
        self.morph_tex: rl.Texture | None = None
        self.gen_hitboxes: dict[str, rl.Rectangle] = {}
        self.hovered_target_idx: int | None = None

        # Active popover editor for a generator image
        self.rec: RingElementConstructor | None = None
        self.editing_gen_idx: int | None = None

        # Validation status
        self.is_valid: bool = False
        self.validation_message: str = "Assign an image for each generator."

        # Action buttons layout
        self._update_button_layout()

        # Typst layout query block
        self.query_block = """
            #context [
            #metadata({
                let positions = (:)
                for i in range(50) {
                let selectors = (
                    "l_" + str(i): label("l_" + str(i)),
                    "r_" + str(i): label("r_" + str(i))
                )
                for (key, sel) in selectors {
                    let matches = query(sel)
                    if matches.len() > 0 {
                    let elem = matches.first()
                    let pos = elem.location().position()
                    let size = elem.value
                    positions.insert(key, (
                        x: pos.x / 1pt,
                        y: pos.y / 1pt,
                        width: size.width,
                        height: size.height
                    ))
                    }
                }
                }
                positions
            })<layout_data>
            ]
        """

        # Compile initial diagram
        self.rebuild_formula()

    def draw_text(self, text: str, x: float, y: float, size: float, color: rl.Color, spacing: float = 1.0) -> None:
        """Helper to draw text using the configured font."""
        rl.draw_text_ex(self.font, text, rl.Vector2(x, y), size, spacing, color)

    def measure_text_w(self, text: str, size: float, spacing: float = 1.0) -> float:
        """Helper to measure text width using the configured font."""
        return rl.measure_text_ex(self.font, text, size, spacing).x

    def _get_sorted_generators(self) -> list[Any]:
        """Returns generators sorted deterministically: 1 first, then polynomials by degree."""
        gens = list(self.domain.generators or [])

        def sort_key(g):
            if isinstance(g, (int, float)):
                return (0, int(g), str(g))
            if hasattr(g, "deg"):
                return (1, g.deg, str(g))
            return (2, 0, str(g))

        gens.sort(key=sort_key)
        return gens

    def _update_button_layout(self) -> None:
        """Calculates positions for bottom action buttons and header."""
        cy = self.card_rect.y + self.card_rect.height - 85.0

        # Close / Back button (top right of card)
        self.btn_exit = rl.Rectangle(
            self.card_rect.x + self.card_rect.width - 170.0,
            self.card_rect.y + 20.0,
            140.0,
            52.0,
        )

        # Bottom buttons
        self.btn_reset = rl.Rectangle(self.card_rect.x + 35.0, cy, 185.0, 56.0)
        self.btn_confirm = rl.Rectangle(
            self.card_rect.x + self.card_rect.width - 340.0,
            cy,
            305.0,
            56.0,
        )

    def rebuild_formula(self) -> None:
        """Constructs and queues the Typst formula for Domain -> Codomain and generator rows."""
        code = f"$ mat(delim: #none,\n"
        code += f"  {self.domain.typst_str}, stretch(->, size: #250%), {self.codomain.typst_str};\n"

        for i, gen in enumerate(self.generators):
            gen_str = gen.typst_str if hasattr(gen, "typst_str") else str(gen)
            left_target = f'#target("l_{i}", ${gen_str}$)'

            # Right side target image
            if i in self.assigned_images:
                val = self.assigned_images[i].typst_str
                right_target = f'#target("r_{i}", ${val}$)'
            else:
                right_target = f'#target("r_{i}", $?$)'

            code += f"  {left_target}, stretch(|->, size: #250%), {right_target};;\n"

        code += ") $\n"
        self.typst_code = code

        # Trigger background compilation
        self.morph_fut = self.tfr.queue_formula(self.typst_code, 600, query_block=self.query_block)

        # Check validation
        self._validate_homomorphism()

    def _validate_homomorphism(self) -> None:
        """Algebraically verifies whether the assigned images define a valid ring homomorphism."""
        if len(self.assigned_images) < len(self.generators):
            remaining = len(self.generators) - len(self.assigned_images)
            self.is_valid = False
            self.validation_message = f"Assign images for all generators ({remaining} remaining)."
            return

        # All checks passed!
        self.is_valid = True
        self.validation_message = "Well-defined Group Homomorphism! Ready to confirm."

    def _open_element_constructor(self, gen_idx: int, slot_rect: rl.Rectangle) -> None:
        """Opens the RingElementConstructor popover anchored to the clicked slot."""
        gen = self.generators[gen_idx]
        gen_str = gen.typst_str if hasattr(gen, "typst_str") else str(gen)
        current_val = self.assigned_images.get(gen_idx, 0)

        self.editing_gen_idx = gen_idx
        self.rec = RingElementConstructor(
            ring=self.codomain,
            anchor_rect=slot_rect,
            gen_name=gen_str,
            initial_value=current_val,
            on_confirm=lambda val: self._on_image_confirmed(gen_idx, val),
            on_cancel=lambda: self._on_image_cancelled(),
            tfr=self.tfr,
            font=self.font,
        )

    def _on_image_confirmed(self, gen_idx: int, val: int) -> None:
        """Callback when user confirms an image value."""
        self.assigned_images[gen_idx] = val
        self.rec = None
        self.editing_gen_idx = None
        self.rebuild_formula()

    def _on_image_cancelled(self) -> None:
        """Callback when user cancels the popover."""
        self.rec = None
        self.editing_gen_idx = None

    def update(self, dt: float) -> None:
        if self.morph_fut is not None and self.morph_fut.done():
            res = self.morph_fut.result()
            if res.success:
                new_tex = rl.load_texture(str(res.png_path.resolve()))
                if new_tex.id > 0:
                    if self.morph_tex is not None and self.morph_tex.id > 0:
                        rl.unload_texture(self.morph_tex)
                    self.morph_tex = new_tex
                    self.morph_res = res

                    self.gen_hitboxes = get_raylib_rectangles(
                        layout_data=res.layout_data,
                        ppi=600,
                        texture_center_x=self.center_of_morphism.x,
                        texture_center_y=self.center_of_morphism.y,
                        texture_width=self.morph_tex.width,
                        texture_height=self.morph_tex.height,
                    )
            self.morph_fut = None

        if self.rec is not None:
            self.rec.update(dt)
            return

        mouse_pos = rl.get_mouse_position()
        mouse_clicked = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)
        self.hovered_target_idx = None

        for i in range(len(self.generators)):
            target_key = f"r_{i}"
            if target_key in self.gen_hitboxes:
                slot_rect = get_expanded_slot_rect(self.gen_hitboxes[target_key])
                if rl.check_collision_point_rec(mouse_pos, slot_rect):
                    self.hovered_target_idx = i
                    if mouse_clicked:
                        self._open_element_constructor(i, slot_rect)
                        return

        if rl.check_collision_point_rec(mouse_pos, self.btn_exit):
            if mouse_clicked:
                self.game.exit_state()
                return

        if rl.check_collision_point_rec(mouse_pos, self.btn_reset):
            if mouse_clicked:
                self.assigned_images.clear()
                self.rebuild_formula()
                return

        if self.is_valid and rl.check_collision_point_rec(mouse_pos, self.btn_confirm):
            if mouse_clicked:
                if self.on_complete is not None:
                    mapping = {
                        self.generators[i]: self.assigned_images[i]
                        for i in range(len(self.generators))
                    }
                    self.on_complete(mapping)
                    print(f"\n\n{mapping}\n\n")
                self.game.exit_state()
                return

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        mouse_pos = rl.get_mouse_position()

        # 1. Main Slate Card Background & Border
        rl.draw_rectangle_rounded(self.card_rect, 0.03, 14, rl.Color(28, 33, 44, 255))
        rl.draw_rectangle_rounded_lines_ex(
            self.card_rect, 0.03, 14, 2.0, rl.Color(48, 58, 78, 255)
        )

        # 2. Header Title & Subtitle with anti-aliased font
        self.draw_text(
            "Group Homomorphism Constructor",
            self.card_rect.x + 35,
            self.card_rect.y + 24,
            38.0,
            rl.Color(240, 244, 255, 255),
        )
        self.draw_text(
            "Click on any target slot on the right to assign the image for that generator.",
            self.card_rect.x + 35,
            self.card_rect.y + 58,
            28.0,
            rl.Color(140, 155, 180, 255),
        )

        # 3. Exit / Close Button (top-right)
        exit_hover = rl.check_collision_point_rec(mouse_pos, self.btn_exit)
        exit_bg = rl.Color(50, 58, 76, 255) if exit_hover else rl.Color(38, 44, 58, 255)
        rl.draw_rectangle_rounded(self.btn_exit, 0.25, 6, exit_bg)
        rl.draw_rectangle_rounded_lines_ex(self.btn_exit, 0.25, 6, 1.0, rl.Color(75, 88, 115, 255))
        exit_txt = "Close"
        et_w = self.measure_text_w(exit_txt, 30.0)
        self.draw_text(
            exit_txt,
            self.btn_exit.x + (self.btn_exit.width - et_w) / 2.0,
            self.btn_exit.y + (self.btn_exit.height - 30.0) / 2.0,
            30.0,
            rl.Color(200, 210, 230, 255),
        )

        # 4. Render Typst Mathematical Formula Texture in crisp white!
        if self.morph_tex is not None:
            topleft_x = int(self.center_of_morphism.x - (self.morph_tex.width / 2))
            topleft_y = int(self.center_of_morphism.y - (self.morph_tex.height / 2))
            rl.draw_texture(self.morph_tex, topleft_x, topleft_y, rl.WHITE)

        # 5. Render Interactive Target Sockets
        for i in range(len(self.generators)):
            target_key = f"r_{i}"
            if target_key in self.gen_hitboxes:
                slot_rect = get_expanded_slot_rect(self.gen_hitboxes[target_key])
                is_hovered = self.hovered_target_idx == i
                is_assigned = i in self.assigned_images

                if is_assigned:
                    slot_bg = (
                        rl.Color(16, 185, 129, 45) if self.is_valid else rl.Color(14, 116, 144, 45)
                    )
                    slot_border = (
                        rl.Color(16, 185, 129, 255) if is_hovered else rl.Color(56, 189, 248, 220)
                    )
                    border_w = 2.0 if is_hovered else 1.5
                else:
                    slot_bg = rl.Color(42, 50, 70, 200) if is_hovered else rl.Color(32, 38, 54, 150)
                    slot_border = rl.Color(56, 189, 248, 255) if is_hovered else rl.Color(70, 85, 115, 180)
                    border_w = 2.0 if is_hovered else 1.2

                rl.draw_rectangle_rounded(slot_rect, 0.35, 8, slot_bg)
                rl.draw_rectangle_rounded_lines_ex(slot_rect, 0.35, 8, border_w, slot_border)

                # Tooltip / hover hint
                if is_hovered and self.rec is None:
                    hint = "Click to edit" if is_assigned else "Click to set image"
                    hw = self.measure_text_w(hint, 26.0)
                    self.draw_text(
                        hint,
                        slot_rect.x + (slot_rect.width - hw) / 2.0,
                        slot_rect.y - 32,
                        26.0,
                        rl.Color(56, 189, 248, 255),
                    )

        # 6. Bottom Bar: Reset, Validation Status, and Confirm Morphism
        cy = self.card_rect.y + self.card_rect.height - 85.0

        # Reset button
        reset_hover = rl.check_collision_point_rec(mouse_pos, self.btn_reset)
        reset_bg = rl.Color(50, 58, 76, 255) if reset_hover else rl.Color(38, 44, 58, 255)
        rl.draw_rectangle_rounded(self.btn_reset, 0.25, 6, reset_bg)
        rl.draw_rectangle_rounded_lines_ex(self.btn_reset, 0.25, 6, 1.0, rl.Color(75, 88, 115, 255))
        rst_txt = "Clear All"
        rw = self.measure_text_w(rst_txt, 30.0)
        self.draw_text(
            rst_txt,
            self.btn_reset.x + (self.btn_reset.width - rw) / 2.0,
            self.btn_reset.y + (self.btn_reset.height - 30.0) / 2.0,
            30.0,
            rl.Color(200, 210, 230, 255),
        )

        # Validation status banner
        status_color = rl.Color(16, 185, 129, 255) if self.is_valid else rl.Color(245, 158, 11, 255)
        self.draw_text(
            self.validation_message,
            self.btn_reset.x + self.btn_reset.width + 30.0,
            cy + (self.btn_reset.height - 29.0) / 2.0,
            29.0,
            status_color,
        )

        # Confirm Morphism button
        if self.is_valid:
            conf_hover = rl.check_collision_point_rec(mouse_pos, self.btn_confirm)
            conf_bg = rl.Color(16, 185, 129, 255) if conf_hover else rl.Color(5, 150, 105, 255)
            conf_border = rl.Color(52, 211, 153, 255)
            text_col = rl.WHITE
        else:
            conf_bg = rl.Color(40, 48, 64, 255)
            conf_border = rl.Color(60, 72, 96, 255)
            text_col = rl.Color(120, 135, 160, 255)

        rl.draw_rectangle_rounded(self.btn_confirm, 0.25, 6, conf_bg)
        rl.draw_rectangle_rounded_lines_ex(self.btn_confirm, 0.25, 6, 1.2, conf_border)
        cf_txt = "Confirm Morphism"
        cw = self.measure_text_w(cf_txt, 30.0)
        self.draw_text(
            cf_txt,
            self.btn_confirm.x + (self.btn_confirm.width - cw) / 2.0,
            self.btn_confirm.y + (self.btn_confirm.height - 30.0) / 2.0,
            30.0,
            text_col,
        )

        # 7. Render Active Popover (on top of everything)
        if self.rec is not None:
            self.rec.render(logical_texture)


def get_expanded_slot_rect(rect: rl.Rectangle, pad_x: float = 16.0, pad_y: float = 12.0) -> rl.Rectangle:
    """Creates a generous, easy-to-click target socket rectangle centered around a Typst symbol."""
    w = max(rect.width + pad_x * 2.0, 70.0)
    h = max(rect.height + pad_y * 2.0, 44.0)
    x = rect.x + (rect.width - w) / 2.0
    y = rect.y + (rect.height - h) / 2.0
    return rl.Rectangle(x, y, w, h)


def get_raylib_rectangles(
    layout_data: dict[str, dict[str, float]],
    ppi: int,
    texture_center_x: float,
    texture_center_y: float,
    texture_width: float,
    texture_height: float,
) -> dict[str, rl.Rectangle]:
    """Converts Typst layout points into accurate Raylib screen rectangles."""
    pt_to_pixel_scale = ppi / 72.0
    texture_top_left_x = texture_center_x - (texture_width / 2.0)
    texture_top_left_y = texture_center_y - (texture_height / 2.0)

    raylib_rects = {}
    for label_name, geo in layout_data.items():
        w = geo["width"] * pt_to_pixel_scale
        h = geo["height"] * pt_to_pixel_scale
        raw_x = texture_top_left_x + (geo["x"] * pt_to_pixel_scale)
        raw_y = texture_top_left_y + (geo["y"] * pt_to_pixel_scale)
        screen_x = raw_x - w
        screen_y = raw_y - h
        raylib_rects[label_name] = rl.Rectangle(screen_x, screen_y, w, h)

    return raylib_rects
