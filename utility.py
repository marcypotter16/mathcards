import pyray as rl


def draw_fitted_texture(tex: rl.Texture, bounding_box: rl.Rectangle) -> None:
    """Draws a texture centered in a bounding box, scaling down only if it overflows."""
    if tex is None or tex.id <= 0:
        return

    max_w = bounding_box.width * 0.85
    max_h = bounding_box.height * 0.85
    
    scale_w = max_w / tex.width
    scale_h = max_h / tex.height
    
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


# fixtures/make_game_state2.py


