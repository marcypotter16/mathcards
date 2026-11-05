import asyncio
from concurrent.futures import Future

import pyray as rl

from Settings import FONT_PATH, WINDOW
from entities.GameUI import GameUI
from states.menu import MainMenuState
from states.morphism import MorphismConstructorState
from game import Game
from mathematics.poly import Polynomial
from mathematics.ring import QQ, ZZ, IntegerIdeal, Localization, PolyRing, PolyRingQuot, PrincipalPolyIdeal, ZZn
from states.test import TestState
from tfr import FormulaResult, TypstFormulaRenderer

SWW, LWW, SWH, LWH = WINDOW["S_WIDTH"], WINDOW["L_WIDTH"], WINDOW["S_HEIGHT"], WINDOW["L_HEIGHT"]
SCREEN_SCALING = (float(SWW) / LWW, float(SWH) / LWH)

BACKGROUND = WINDOW["BG_COLOR"]

game:       Game

def update():
    global game
    dt = rl.get_frame_time()
    game.update(dt)

async def main() -> None:
    rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE | rl.ConfigFlags.FLAG_VSYNC_HINT | rl.ConfigFlags.FLAG_MSAA_4X_HINT)
    rl.set_trace_log_level(5)
    rl.set_target_fps(120)
    rl.init_window(SWW, SWH, "Mathcards")
    icon            = rl.load_image("Generated icon.png")
    rl.set_window_icon(icon)
    LOGICAL_TEXTURE = rl.load_render_texture(LWW, LWH)
    tfr = TypstFormulaRenderer()
    game = Game(tfr)
    game.init()

    GAME_FONT = rl.load_font(FONT_PATH)
    # game_ui         = GameUI()
    # init_cards()
    # formula_card    = await FormulaCard.create("$ZZ[x]/(x^2)$", tfr=tfr)
    # fc2             = await FormulaCard.create("$ZZ$", tfr=tfr)
    # formula_card.place_card(Vector2(300, 400))
    # fc2.place_card(Vector2(300, 550))
    # card_manager.spawn_card(formula_card, 0)
    # card_manager.spawn_card(fc2, 1)

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
            update()
            rl.begin_drawing()
            rl.begin_texture_mode(LOGICAL_TEXTURE)

            rl.clear_background(BACKGROUND)
            # game_ui.render()
            # card_manager.render(LOGICAL_TEXTURE)
            # mc.render()
            game.render(LOGICAL_TEXTURE)
            rl.end_texture_mode()
            source_rect = rl.Rectangle(0, 0, LWW, -LWH)
            dest_rect = rl.Rectangle(0, 0, rl.get_screen_width(), rl.get_screen_height())
            rl.draw_texture_pro(LOGICAL_TEXTURE.texture, source_rect, dest_rect, rl.Vector2(0, 0), 0, rl.WHITE)
            rl.end_drawing()
    finally:
        # if texture.id > 0:
        #     rl.unload_texture(texture)
        rl.unload_render_texture(LOGICAL_TEXTURE)
        # card_manager.unload()
        game.unload()
        rl.close_window()


if __name__ == "__main__":
    asyncio.run(main())
