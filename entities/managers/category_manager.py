import pyray as rl
from pyray import RenderTexture

from entities.base import Entity
from entities.game_manager.dataclasses import GameView
from mathematics.base import Category
from mathematics.vector import Vector2
from state_manager import StateManager


class CategoryManager(Entity):
    def __init__(self, center: Vector2, sm: StateManager, gw: GameView, initial_cat: Category) -> None:
        super().__init__()
        self.gw = gw
        self.center = center
        self.topleft = None
        self.sm = sm
        self.cat = initial_cat
        form = f"""#show math.equation.where(block: true): set block(above: 3pt, below: 0pt)
            #text(size: 6pt)[
            Current Category:
            ] $ bb(upright("{self.cat.name}")) $"""
        self.ff = self.sm.tfr.queue_formula(form, 400, frac_inline=False)
        self.tex = None

    def sync(self, gw: GameView):
        if self.cat == Category(gw.active_category):
            return
        self.tex = None
        self.cat = Category(gw.active_category)
        form = f"""#show math.equation.where(block: true): set block(above: 3pt, below: 0pt)
            #text(size: 6pt)[
            Current Category:
            ] $ bb(upright("{self.cat.name}")) $"""
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

    def render(self, logical_texture: RenderTexture | None) -> None:
        if self.tex is not None and self.topleft is not None:
            rl.draw_texture(self.tex, int(self.topleft.x), int(self.topleft.y), rl.RAYWHITE)