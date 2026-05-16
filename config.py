import os
from dotenv import load_dotenv

load_dotenv()

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
PLACEHOLDER = os.getenv("PLACEHOLDER", os.path.join(os.path.dirname(__file__), "assets", "placeholder.jpg"))
FONT = os.getenv("FONT", os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Medium.ttf"))

THEME = {
    "fonts": {
        "size_title": 22,
        "size_meta": 16,
        "size_meta_sm": 12,
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
        "status_idle": (160, 160, 160),
        "status_err": (255, 80, 80),
        "screen_dim": 0.1
    },
    "layout": {
        # The image size to request from Jellyfin
        # It will be scaled to fit the max width and height while maintaining aspect ratio
        "art": {
            "max_width": 320,
            "max_height": 160,
            "border": 4 # Around the artwork, in pixels
        },
        "temp": {
            "right": 10,
            "bottom": 20
        },
        "icon": {
            "left": 10,
            "top": 10
        },
        "music": {
            "left": 10,
            "right": 10,
            "title_top": 8, # Relative to artwork bottom
            "artist_top": 36, # Relative to artwork bottom
            "year_top": 58 # Relative to artwork bottom
        },
        "video": {
            "left": 10,
            "right": 10,
            "title_top": 12, # Relative to artwork bottom
            "year_top": 30 # Relative to artwork bottom
        },
        "generic": {
            "left": 10,
            "right": 10,
            "title_top": 12, # Relative to artwork bottom
        },
    },
    "strings": {
        "idle": "JELLYHAT IDLE"
    }
}