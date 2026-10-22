import asyncio
from concurrent.futures import Future

import pyray as rl

from GameEntities.Card import Card, Suit, init_cards
from GameEntities.CardManager import CardManager
from GameEntities.Entity import Entity
from GameEntities.FormulaCard import FormulaCard
from Vector import Vector2
from typst_formula_renderer import FormulaResult, TypstFormulaRenderer


# LOGICAL DIMENSIONS
L_WINDOW_WIDTH = 1920
L_WINDOW_HEIGHT = 1080

# SCREEN DIMENSIONS
S_WINDOW_WIDTH = 1920
S_WINDOW_HEIGHT = 1080

SCREEN_SCALING = (float(S_WINDOW_WIDTH) / L_WINDOW_WIDTH, float(S_WINDOW_HEIGHT) / L_WINDOW_HEIGHT)

BACKGROUND = rl.Color(24, 26, 32, 255)

entities: list[Entity] = []
card_manager:       CardManager         = CardManager()
formula_card:       FormulaCard | None  = None

def update():
    dt = rl.get_frame_time()
    for entity in entities:
        entity.update(dt)
    card_manager.update(dt)

async def main() -> None:
    rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_RESIZABLE | rl.ConfigFlags.FLAG_VSYNC_HINT | rl.ConfigFlags.FLAG_MSAA_4X_HINT)
    rl.set_target_fps(120)
    rl.init_window(S_WINDOW_WIDTH, S_WINDOW_HEIGHT, "Mathcards")
    LOGICAL_TEXTURE = rl.load_render_texture(L_WINDOW_WIDTH, L_WINDOW_HEIGHT)
    # init_cards()
    formula_card    = await FormulaCard.create("$ZZ[x]/(x^2)$")
    fc2             = await FormulaCard.create("$ZZ$", "integers")
    formula_card.place_card(Vector2(300, 400))
    fc2.place_card(Vector2(300, 550))
    card_manager.spawn_card(formula_card, 0)
    card_manager.spawn_card(fc2, 1)

    try:
        while not rl.window_should_close():
            update()
            rl.begin_drawing()
            rl.begin_texture_mode(LOGICAL_TEXTURE)

            rl.clear_background(BACKGROUND)
            card_manager.render(LOGICAL_TEXTURE)
            rl.end_texture_mode()
            source_rect = rl.Rectangle(0, 0, L_WINDOW_WIDTH, -L_WINDOW_HEIGHT)
            dest_rect = rl.Rectangle(0, 0, rl.get_screen_width(), rl.get_screen_height())
            rl.draw_texture_pro(LOGICAL_TEXTURE.texture, source_rect, dest_rect, rl.Vector2(0, 0), 0, rl.WHITE)
            rl.end_drawing()
    finally:
        # if texture.id > 0:
        #     rl.unload_texture(texture)
        rl.unload_render_texture(LOGICAL_TEXTURE)
        card_manager.unload()
        rl.close_window()


if __name__ == "__main__":
    asyncio.run(main())
