import pyray as rl

# 1. YOUR FIXED VIRTUAL / LOGICAL RESOLUTION
# Design everything as if you are building for 1080p.
L_WINDOW_WIDTH = 1920
L_WINDOW_HEIGHT = 1080

# 2. INITIAL WINDOW SIZE (Matches logical, or whatever starting size you want)
# Use a size that fits comfortably on a standard monitor, and allow resizing.
S_WINDOW_WIDTH = 1920
S_WINDOW_HEIGHT = 1080

BACKGROUND = rl.Color(24, 26, 32, 255)

def update():
    dt = rl.get_frame_time()
    # for entity in entities:
    #     entity.update(dt)

def main() -> None:
    rl.set_config_flags(
        rl.ConfigFlags.FLAG_WINDOW_RESIZABLE | 
        rl.ConfigFlags.FLAG_VSYNC_HINT | 
        rl.ConfigFlags.FLAG_MSAA_4X_HINT
    )
    rl.set_target_fps(60)
    
    # Create a window of a reasonable physical size
    rl.init_window(S_WINDOW_WIDTH, S_WINDOW_HEIGHT, "Mathcards")
    
    # Load your virtual canvas (Always 1920x1080)
    logical_texture = rl.load_render_texture(L_WINDOW_WIDTH, L_WINDOW_HEIGHT)
    
    try:
        while not rl.window_should_close():
            update()
            
            # Dynamically calculate scaling based on current window size (handles resizing!)
            current_width = rl.get_screen_width()
            current_height = rl.get_screen_height()
            
            scale_x = float(current_width) / L_WINDOW_WIDTH
            scale_y = float(current_height) / L_WINDOW_HEIGHT

            # --- RENDERING PHASE ---
            rl.begin_drawing()
            
            # 1. Draw everything to the virtual logical texture
            rl.begin_texture_mode(logical_texture)
            rl.clear_background(BACKGROUND)
            
            # ---> DRAW YOUR GAME CODE HERE (using 1920x1080 coordinates) <---
            rl.draw_text("Hello Resolution Independence!", 100, 100, 40, rl.WHITE)
            
            rl.end_texture_mode()

            # 2. Draw the virtual texture onto the actual screen, scaled and flipped for OpenGL
            # (OpenGL render textures are vertically flipped, so we use a negative source height)
            source_rect = rl.Rectangle(0, 0, L_WINDOW_WIDTH, -L_WINDOW_HEIGHT)
            dest_rect = rl.Rectangle(0, 0, current_width, current_height)
            
            rl.draw_texture_pro(
                logical_texture.texture, 
                source_rect, 
                dest_rect, 
                rl.Vector2(0, 0), 
                0.0, 
                rl.WHITE
            )
            
            rl.end_drawing()
            
    finally:
        rl.unload_render_texture(logical_texture)
        rl.close_window()

if __name__ == "__main__":
    main()