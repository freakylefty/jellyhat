import os
from dotenv import load_dotenv

load_dotenv()

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")

THEME = {
    "fonts": {
        "path": "fonts/Roboto-Medium.ttf",
        "size_title": 22,
        "size_meta": 16,
        "size_status": 18
    },
    "colors": {
        "background": (0, 0, 0),
        "text_main": (255, 255, 255),
        "text_dim": (160, 160, 160),
        "temp_text_normal": (255, 165, 0),
        "temp_text_hot": (255, 0, 0),
        "temp_led_hot": (255, 0, 0),
        "temp_led_normal": (0, 0, 0),
        "temp_led_off": (0, 0, 0),
        "status_idle": (80, 80, 80),
        "status_err": (255, 80, 80),
    },
    "layout": {
        "art_max_width": 320,
        "art_max_height": 160,
        "text_x": 10,
        "title_y": 8,
        "artist_y": 32,
        "temp_y": 54,
        "border": 4
    },
    "strings": {
        "idle": "JELLYHAT IDLE",
        "play_symbol": ">",
        "pause_symbol": "="
    }
}