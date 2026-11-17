import pyray as rl
from pyray import RenderTexture

from entities.base import Entity
from entities.card.base import BaseCard
from entities.card.eor_card import RingElementCard
from entities.game_manager.actions import (
    CardEndedDragging,
    CardRingConverted,
    CardStartedDragging,
)
from entities.game_manager.dataclasses import GameView
from entities.game_manager.events import EVENT_BUS
from entities.printer import Printer
from interfaces import DropResult, DropZone
from mathematics.base import CommUnitRing
from mathematics.canonical_maps import Conversion
from mathematics.serialization import serialize_ring
from mathematics.vector import Vector2
from state_manager import StateManager


class RingManager(Entity, DropZone):
    def __init__(self, center: Vector2, sm: StateManager, gw: GameView, initial_ring: CommUnitRing) -> None:
        super().__init__()
        self.gw = gw
        self.center = center
        self.topleft = None
        self.sm = sm
        self.ring = initial_ring
        form = f"""#show math.equation.where(block: true): set block(above: 3pt, below: 0pt)
            #text(size: 6pt)[
            Current Structure:
            ] $ {self.ring.typst_str} $"""
        self.ff = self.sm.tfr.queue_formula(form, 400, frac_inline=False)
        self.tex = None
        self.draw_rect = False
        self.rect = rl.Rectangle()
        EVENT_BUS.subscribe(CardStartedDragging, self._handle_card_started_dragging)

    @property
    def is_ready(self) -> bool:
        return self.tex is not None

    def can_convert(self, card: BaseCard) -> tuple[bool, str | None]:
        if not isinstance(card, RingElementCard):
            return False, "only ring elements can be converted"
        r1 = card.ring
        r2 = self.gw.active_ring
        if r1 == r2:
            return False, f"trying to convert an element that is already in {r2}"
        mor = Conversion.try_get(r1, r2)
        if mor is None:
            return False, f"no canonical map from {r1} to {r2}"
        return True, None

    def try_accept_drop(self, act: CardEndedDragging) -> DropResult:
        self.draw_rect = False
        inside = rl.check_collision_point_rec(act.position.raylib_ref, self.rect)
        if not inside:
            return DropResult.Outside
        ok, err = self.can_convert(act.card)
        if not ok:
            Printer.print(err)
            return DropResult.InsideInvalid
        EVENT_BUS.emit(CardRingConverted(self.gw.me, act.card.card_id, serialize_ring(self.ring)))
        return DropResult.Accepted

    def _handle_card_started_dragging(self, act: CardStartedDragging):
        if isinstance(act.card, RingElementCard):
            self.draw_rect = True

    def sync(self, gw: GameView):
        # Printer.print(self.ring, gw.active_ring)
        if self.ring == gw.active_ring:
            return
        self.tex = None
        self.ring = gw.active_ring
        form = f"""#show math.equation.where(block: true): set block(above: 3pt, below: 0pt)
            #text(size: 6pt)[
            Current Structure:
            ] $ {self.ring.typst_str} $"""
        self.ff = self.sm.tfr.queue_formula(form, 400, frac_inline=False)

    def update(self, dt: float) -> None:
        if self.tex is None and self.ff.done():
            res = self.ff.result()
            self.tex = rl.load_texture(str(res.png_path.resolve()))
            rl.set_texture_filter(self.tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
            self.topleft = Vector2(
                int(self.center.x - self.tex.width * .5),
                int(self.center.y - self.tex.height * .5)
            )
            self.rect = rl.Rectangle(
                self.topleft.x,
                self.topleft.y,
                self.tex.width,
                self.tex.height
            )

    def render(self, logical_texture: RenderTexture | None) -> None:
        if self.tex is not None and self.topleft is not None:
            rl.draw_texture(self.tex, int(self.topleft.x), int(self.topleft.y), rl.RAYWHITE)
            if self.draw_rect:
                rl.draw_rectangle_lines_ex(
                    self.rect,
                    2,
                    rl.GREEN
                )
