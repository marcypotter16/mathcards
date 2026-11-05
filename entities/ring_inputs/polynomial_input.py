# entities/ring_inputs/polynomial_input.py
"""
Input popover for PolyRing and PolyRingQuot ring elements.

Two-phase flow:
  Phase 1 – Degree selection (skipped for PolyRingQuot, whose degree is fixed).
             User picks a degree d in [1..5] with a stepper, then presses Confirm.
  Phase 2 – Coefficient input.
             A Typst formula showing  a_0 + a_1 x + … + a_{d-1} x^{d-1}  with "?"
             for unfilled coefficients is rendered as a PNG texture.
             Each coefficient slot is a clickable button that spawns the appropriate
             sub-widget for the coefficient ring (IntegerInput for ZZ/ZZn,
             FractionInput for QQ/FractionField/Localization, etc.).
             When the sub-widget confirms, the value is stored and the preview
             texture is re-queued.
"""
from concurrent.futures import Future
from typing import Any, Callable

import pyray as rl

from entities.ring_inputs.base import BaseElementInput
from mathematics.base import CommUnitRing, get_rect_center
from mathematics.ring import ZZ, ZZn, QQ, FractionField, Localization, PolyRing, PolyRingQuot
from mathematics.poly import Polynomial
from tfr import FormulaResult, TypstFormulaRenderer


# ---------------------------------------------------------------------------
# Typst formula builder
# ---------------------------------------------------------------------------

def _build_typst_poly(degree: int, coeffs: list[Any | None]) -> str:
    """
    Returns a Typst math-mode string for a polynomial of the given degree.

    `coeffs` has length `degree + 1`; an entry of `None` means the slot is
    unfilled and will be rendered as a clickable `square`.

    Produces e.g.  $ #target("c_0", $square$) + #target("c_1", $square$) x $
    """
    terms: list[str] = []
    for d in range(degree + 1):
        val = coeffs[d] if d < len(coeffs) else None

        if val is None:
            c = "square"
        elif hasattr(val, "typst_str"):
            c = val.typst_str
        else:
            c = str(val)

        slot = f"#target(\"c_{d}\", ${c}$)"
        if d == 0:
            terms.append(slot)
        elif d == 1:
            terms.append(f"{slot} x")
        else:
            terms.append(f"{slot} x^{d}")

    body = " + ".join(terms) if terms else "0"
    print(body)
    return f"$ {body} $"

# ---------------------------------------------------------------------------
# Coefficient widget factory
# ---------------------------------------------------------------------------

def _make_coeff_widget(
    coeff_ring:   CommUnitRing,
    anchor_rect:  rl.Rectangle,
    gen_name:     str,
    current_val:  Any,
    on_confirm:   Callable[[Any], None],
    on_cancel:    Callable[[], None],
    tfr:          TypstFormulaRenderer | None,
    font:         rl.Font | None,
) -> BaseElementInput:
    """Instantiate the right input widget for the given coefficient ring."""
    from entities.ring_inputs.integer_input import IntegerInput
    from entities.ring_inputs.fraction_input import FractionInput

    kwargs = dict(
        ring=coeff_ring,
        anchor_rect=anchor_rect,
        gen_name=gen_name,
        initial_value=current_val,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        tfr=tfr,
        font=font,
    )
    match coeff_ring:
        case QQ() | FractionField() | Localization():
            return FractionInput(**kwargs)
        case _:
            # ZZ, ZZn, or anything else — integer stepper
            return IntegerInput(**kwargs)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class PolynomialInput(BaseElementInput):
    """Handles polynomial input for PolyRing and PolyRingQuot."""

    MAX_DEG = 5  # cap for free PolyRing

    def __init__(
        self,
        ring:          PolyRing,
        anchor_rect:   rl.Rectangle | None,
        gen_name:      str,
        initial_value: Any,
        on_confirm:    Callable[[Any], None],
        on_cancel:     Callable[[], None] | None = None,
        tfr:           TypstFormulaRenderer | None = None,
        font:          rl.Font | None = None,
    ) -> None:
        self._coeff_ring = ring.coefficient_ring

        # Coefficient values (parsed ring elements) and their display strings
        self._coeff_vals:  list[Any]  = []
        self._coeff_set:   list[bool] = []   # True if user has confirmed a value

        # Typst texture state
        self._tex_future: Future[FormulaResult] | None = None
        self._tex: rl.Texture | None = None

        # Active coefficient sub-widget (spawned on click)
        self._active_sub:  BaseElementInput | None = None
        self._active_idx:  int = -1

        # Seed from initial value if Polynomial
        self._initial = initial_value

        super().__init__(ring, anchor_rect, gen_name, initial_value, on_confirm, on_cancel, tfr, font)
        self._phase = 1
        self._selected_deg = 0

        # Typst layout query block
        self.query_block = """
            #context [
            #metadata({
                let positions = (:)
                for i in range(50) {
                let selectors = (
                    "c_" + str(i): label("c_" + str(i)),
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

        self._is_texture_dirty = False
        self.coeff_hitboxes:    dict[str, rl.Rectangle] = {}
        self.formula_topleft:   rl.Vector2

    @property
    def n_coeffs(self) -> int:
        return self._selected_deg + 1

    # ---------------------------------------------------------------------- layout

    def _build_layout(self) -> None:
        self._build_phase1_layout()

    def _build_phase1_layout(self) -> None:
        cx = self.rect.x + self.w / 2.0
        cy = (self.content_y + self.content_bot_y) / 2.0 - 10

        field_w, field_h = 80.0, 52.0
        self._p1_box   = rl.Rectangle(cx - field_w / 2.0, cy, field_w, field_h)
        self._p1_minus = rl.Rectangle(cx - field_w / 2.0 - 58, cy, 48, 52)
        self._p1_plus  = rl.Rectangle(cx + field_w / 2.0 + 10, cy, 48, 52)
        self._p1_label_y = cy - 28

    def _build_phase2_layout(self) -> None:
        rx = self.rect.x

        # Reserve top portion for texture preview
        preview_h = 70.0
        self._preview_rect = rl.Rectangle(rx + 16, self.content_y + 4, self.w - 32, preview_h)

    # ---------------------------------------------------------------------- phase 2 init

    def _enter_phase2(self) -> None:
        self._phase       = 2
        n                 = self.n_coeffs
        zero              = self._coeff_ring.zero
        self._coeff_vals  = [zero] * n
        self._coeff_set   = [False] * n

        self._build_phase2_layout()
        self._queue_preview()

    def _spawn_sub_element_constructor(self, label: str, rect: rl.Rectangle) -> None:
        """Spawn the correct coefficient input widget for the clicked slot."""
        from entities.ring_inputs.integer_input import IntegerInput
        from entities.ring_inputs.fraction_input import FractionInput

        # Figure out which coefficient slot was clicked by matching the rect
        idx = int(label[2]) # c_n

        coeff_ring = self._coeff_ring
        current    = self._coeff_vals[idx] if self._coeff_set[idx] else None

        def _on_confirm(value: Any) -> None:
            print("CONFIRMING VALUE", value, "FOR COEFF", idx)
            print("  self is:", id(self), " coeff_set is:", id(self._coeff_set))
            self._coeff_vals[idx] = value
            self._coeff_set[idx]  = True
            print("  after write:", self._coeff_set)
            print("PRINTING COEFF SET / VALS", self._coeff_set, self._coeff_vals,
      "| id(self)=", id(self), "| id(set)=", id(self._coeff_set))
            self._active_sub       = None
            self._active_idx       = -1
            self._queue_preview()

        def _on_cancel() -> None:
            self._active_sub = None
            self._active_idx = -1

        kwargs = dict(
            ring=self._coeff_ring,
            anchor_rect=rect,
            gen_name=f"{self.gen_name}[{idx}]",
            initial_value=current,
            on_confirm=_on_confirm,
            on_cancel=_on_cancel,
            tfr=self.tfr,
            font=self.font,
        )

        match coeff_ring:
            case ZZ() | ZZn():
                sub = IntegerInput(**kwargs) # type: ignore
            case QQ() | FractionField() | Localization():
                sub = FractionInput(**kwargs) # type: ignore
            case PolyRing() | PolyRingQuot():
                raise NotImplementedError(
                    "Nested polynomial coefficients are not supported yet."
                )
            case _:
                raise NotImplementedError(
                    f"No input widget for coefficient ring {type(coeff_ring).__name__}."
                )

        self._active_sub = sub
        self._active_idx = idx

    # ---------------------------------------------------------------------- texture helpers

    def _coeff_display(self, i: int) -> str | None:
        """Return display string for coeff i, or None to show '?'."""
        if not self._coeff_set[i]:
            return None
        if hasattr(self._coeff_vals[i], "typst_str"):
            return self._coeff_vals[i].typst_str
        return str(self._coeff_vals[i])

    def _queue_preview(self) -> None:
        if self.tfr is None:
            return
        display = [self._coeff_display(i) for i in range(self.n_coeffs)]
        formula = _build_typst_poly(self._selected_deg, display)
        self._tex_future = self.tfr.queue_formula(formula, ppi=220, query_block=self.query_block)
        self._is_texture_dirty = True

    def _poll_texture(self) -> None:
        if self._tex_future is None or not self._tex_future.done() or not self._is_texture_dirty:
            return
        res = self._tex_future.result()
        self._tex_future = None
        if res.success:
            new_tex = rl.load_texture(str(res.png_path.resolve()))
            rl.set_texture_filter(new_tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
            if self._tex is not None:
                rl.unload_texture(self._tex)
            self._tex = new_tex
            center = get_rect_center(self._preview_rect)
            self.formula_topleft = rl.Vector2(center.x - self._tex.width / 2, center.y - self._tex.height / 2)
            self.coeff_hitboxes = get_raylib_rectangles(
                layout_data=res.layout_data,
                ppi=220,
                texture_center_x=center.x,
                texture_center_y=center.y,
                texture_width=self._tex.width,
                texture_height=self._tex.height 
            )
        self._is_texture_dirty = False

    # ---------------------------------------------------------------------- update

    # Override the full update so that when a sub-widget is active all input
    # (including Enter/Escape) is routed exclusively to it.
    def update(self, dt: float) -> None:
        self.cursor_blink_time += dt
        self._poll_texture()

        if self._active_sub is not None:
            self._active_sub.update(dt)
            return

        # No sub-widget active — use base chrome handling + our _update_input
        mouse_pos   = rl.get_mouse_position()
        mouse_click = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        if rl.is_key_pressed(rl.KeyboardKey.KEY_ENTER):
            self._do_confirm(); return
        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self._do_cancel(); return

        if mouse_click:
            inside  = rl.check_collision_point_rec(mouse_pos, self.rect)
            on_anch = self.anchor_rect and rl.check_collision_point_rec(mouse_pos, self.anchor_rect)
            if not inside and not on_anch:
                self._do_cancel(); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_close):
                self._do_cancel(); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_cancel):
                self._do_cancel(); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_confirm):
                self._do_confirm(); return

        self._update_input(dt)

    def _update_input(self, dt: float) -> None:
        if self._phase == 1:
            self._update_phase1()
        else:
            self._update_phase2()

    def _update_phase1(self) -> None:
        mouse_pos   = rl.get_mouse_position()
        mouse_click = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        if rl.is_key_pressed(rl.KeyboardKey.KEY_UP) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_UP):
            self._selected_deg = min(self.n_coeffs, self.MAX_DEG)
        elif rl.is_key_pressed(rl.KeyboardKey.KEY_DOWN) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_DOWN):
            self._selected_deg = max(self._selected_deg - 1, 1)

        if mouse_click:
            if rl.check_collision_point_rec(mouse_pos, self._p1_plus):
                self._selected_deg = min(self.n_coeffs, self.MAX_DEG)
            elif rl.check_collision_point_rec(mouse_pos, self._p1_minus):
                self._selected_deg = max(self._selected_deg - 1, 0)

    def _update_phase2(self) -> None:
        mouse_pos   = rl.get_mouse_position()
        mouse_click = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        if mouse_click:
            for label, rect in self.coeff_hitboxes.items():
                if rl.check_collision_point_rec(mouse_pos, rect):
                    self._spawn_sub_element_constructor(label, rect)

    # ---------------------------------------------------------------------- confirm/cancel

    def _do_confirm(self) -> None:
        if self._phase == 1:
            self._enter_phase2()
        else:
            super()._do_confirm()

    # ---------------------------------------------------------------------- render

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        # Draw own chrome + input area first
        super().render(logical_texture)
        # Draw active sub-widget on top
        if self._active_sub is not None:
            self._active_sub.render(logical_texture)

    def _render_input_area(self, mouse_pos: rl.Vector2) -> None:
        if self._phase == 1:
            self._render_phase1(mouse_pos)
        else:
            self._render_phase2(mouse_pos)

    def _render_phase1(self, mouse_pos: rl.Vector2) -> None:
        rx = self.rect.x
        self.draw_text("Select polynomial degree:", rx + 22, self._p1_label_y, 18.0, self.COL_SUBTITLE)

        for btn, sym in [(self._p1_minus, "-"), (self._p1_plus, "+")]:
            hover = rl.check_collision_point_rec(mouse_pos, btn)
            rl.draw_rectangle_rounded(btn, 0.2, 6, self.COL_STEPPER_H if hover else self.COL_STEPPER_BG)
            rl.draw_rectangle_rounded_lines_ex(btn, 0.2, 6, 1.2, self.COL_STEPPER_BRD)
            sw = self.measure_text_w(sym, 28.0)
            self.draw_text(sym, btn.x + (btn.width - sw) / 2.0, btn.y + (btn.height - 28.0) / 2.0, 28.0, rl.WHITE)

        rl.draw_rectangle_rounded(self._p1_box, 0.2, 6, self.COL_FIELD_BG)
        rl.draw_rectangle_rounded_lines_ex(self._p1_box, 0.2, 6, 1.5, self.COL_FIELD_BORDER)
        dstr = str(self._selected_deg)
        dw = self.measure_text_w(dstr, 32.0)
        self.draw_text(dstr,
            self._p1_box.x + (self._p1_box.width - dw) / 2.0,
            self._p1_box.y + (self._p1_box.height - 32.0) / 2.0,
            32.0, rl.WHITE)

        hint = f"(max {self.MAX_DEG})  — press Confirm to proceed"
        hw = self.measure_text_w(hint, 14.0)
        self.draw_text(hint,
            self.rect.x + (self.w - hw) / 2.0,
            self._p1_box.y + self._p1_box.height + 12,
            14.0, self.COL_SUBTITLE)

    def _render_phase2(self, mouse_pos: rl.Vector2) -> None:
        # BUG: UNDERSTAND WHY THE FUCK DOES THE FIRST COEFFICIENT (C_0) HAVE A SLIGHTLY OFFSET COEFFICIENT RECT
        # ---- Preview texture ------------------------------------------------
        pr = self._preview_rect
        rl.draw_rectangle_rounded(pr, 0.12, 8, rl.Color(16, 20, 28, 200))
        rl.draw_rectangle_rounded_lines_ex(pr, 0.12, 8, 1.0, rl.Color(70, 85, 115, 150))

        if self._tex is not None:
            rl.draw_texture_v(self._tex, self.formula_topleft, rl.WHITE)
        elif self._tex_future is not None:
            dots = "." * (1 + int(self.cursor_blink_time) % 3)
            self.draw_text(f"rendering{dots}", pr.x + 12, pr.y + (pr.height - 18.0) / 2.0, 18.0, self.COL_SUBTITLE)

        # if self.coeff_hitboxes:
        #     for lab, rect in self.coeff_hitboxes.items():
        #         rl.draw_rectangle_rec(rect, rl.RED)

    def current_value(self) -> Polynomial:
        coeffs: dict[int, Any] = {}
        for i in range(self.n_coeffs):
            if self._coeff_set[i]:
                c = self._coeff_vals[i]
            else:
                zero = self._coeff_ring.zero
                c = zero
            coeffs[i] = c
        return Polynomial(coeffs, self._coeff_ring)

    # ---------------------------------------------------------------------- cleanup

    def __del__(self) -> None:
        if self._tex is not None:
            try:
                rl.unload_texture(self._tex)
            except Exception:
                pass


def get_expanded_slot_rect(rect: rl.Rectangle, pad_x: float = 16.0, pad_y: float = 8.0) -> rl.Rectangle:
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