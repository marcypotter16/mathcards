import asyncio
from concurrent.futures import Future

import pyray as rl

from Settings import WINDOW
# from entities.GameUI import GameUI
from cached import Cache
from entities.printer import Printer
from states.menu import MainMenuState
from states.morphism import MorphismConstructorState
from state_manager import StateManager
from mathematics.poly import Polynomial
from mathematics.ring import QQ, ZZ, IntegerIdeal, Localization, PolyRing, PolyRingQuot, PrincipalPolyIdeal, ZZn
from states.test import TestState
from tfr import TypstFormulaRenderer

SWW, LWW, SWH, LWH = WINDOW["S_WIDTH"], WINDOW["L_WIDTH"], WINDOW["S_HEIGHT"], WINDOW["L_HEIGHT"]
SCREEN_SCALING = (float(SWW) / LWW, float(SWH) / LWH)

BACKGROUND = WINDOW["BG_COLOR"]

def update(game):
    dt = rl.get_frame_time()
    game.update(dt)
    Printer.update(dt)

async def main() -> None:
    rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE | rl.ConfigFlags.FLAG_VSYNC_HINT | rl.ConfigFlags.FLAG_MSAA_4X_HINT)
    rl.set_trace_log_level(5)
    rl.set_target_fps(120)
    rl.init_window(SWW, SWH, "Mathcards")
    # rl.toggle_fullscreen()
    icon            = rl.load_image("Generated icon.png")

    rl.set_window_icon(icon)
    LOGICAL_TEXTURE = rl.load_render_texture(LWW, LWH)
    Cache.init()

    tfr             = TypstFormulaRenderer()
    game            = StateManager(tfr)
    game.init()
    Printer.init(game.font)

    zz = ZZ()
    zz5 = ZZn(5)
    zz5x = PolyRing(zz5)
    qq = QQ()
    zz_2 = Localization(zz, IntegerIdeal({2}, zz))
    zz5x_q = PolyRingQuot(zz5, PrincipalPolyIdeal(Polynomial({3: 1, 1: 2, 0: 4}, zz5), zz5))
    global mc
    mc = MorphismConstructorState(game, zz5x_q, zz_2, on_complete=lambda d: print(len(d)))

    menu = MainMenuState(game)
    # game.enter_state(menu)
    # game.enter_state(mc)
    t = TestState(game)
    game.enter_state(t)

    try:
        while not rl.window_should_close():
            update(game)
            rl.begin_drawing()
            rl.begin_texture_mode(LOGICAL_TEXTURE)

            rl.clear_background(BACKGROUND)
            # # game_ui.render()
            # # card_manager.render(LOGICAL_TEXTURE)
            # # mc.render()
            game.render(LOGICAL_TEXTURE)
            Printer.render(LOGICAL_TEXTURE)
            rl.end_texture_mode()
            source_rect = rl.Rectangle(0, 0, LWW, -LWH)
            dest_rect = rl.Rectangle(0, 0, rl.get_screen_width(), rl.get_screen_height())
            rl.draw_texture_pro(LOGICAL_TEXTURE.texture, source_rect, dest_rect, rl.Vector2(0, 0), 0, rl.WHITE)
            rl.end_drawing()
    finally:
        # if texture.id > 0:
        #     rl.unload_texture(texture)
        # card_manager.unload()
        rl.unload_render_texture(LOGICAL_TEXTURE)
        game.unload()
        rl.close_window()


if __name__ == "__main__":
    asyncio.run(main())
    # main()
