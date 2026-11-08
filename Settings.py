import pyray as rl

FONT_PATH = "C:\\Users\\marcello\\Documents\\fonts\\Libron-Regular.ttf"

WINDOW = {
    "L_WIDTH": 1920,
    "L_HEIGHT": 1080,
    "S_WIDTH": 1920,
    "S_HEIGHT": 1080,
    # "BG_COLOR": rl.Color(24, 26, 32, 255)
    "BG_COLOR": rl.Color(23, 46, 38, 255)  
}

def get_complementary_color(c: rl.Color) -> rl.Color:
    return rl.Color(255-c.r,255-c.g,255-c.b,255)

def get_dimmed_color(c: rl.Color) -> rl.Color:
    factor = 1.2
    return rl.Color(int(c.r/factor), int(c.g/factor), int(c.b/factor), 255)

# --- Element Colors ---
COLOR_INTEGER    = rl.Color(215, 91, 54, 255) # White
COLOR_FRACTION   = rl.Color(54, 120, 181, 255) # Light Blue
COLOR_POLYNOMIAL = rl.Color(38, 122, 103, 255) # Light Green
COLOR_ZMOD       = rl.Color(50, 159, 134, 255) # Light Orange/Peach

# --- Operator Colors (Saturated) ---
# COLOR_OP_ADD     = rl.Color(255, 140, 105, 255) # Coral/Orange
# COLOR_OP_SUB     = rl.Color(135, 180, 255, 255) # Blue
# COLOR_OP_MUL     = rl.Color(120, 200, 160, 255) # Teal/Green
# COLOR_OP_INVERT  = rl.Color(190, 150, 255, 255) # Purple
COLOR_OP        = rl.Color(112, 85, 160, 255)