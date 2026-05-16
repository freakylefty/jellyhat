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
        "art_max_width": 320,
        "art_max_height": 160,
        # Horiztonal insets for the text from the left edge of the display
        "icon_inset": 10, 
        "info_inset": 34,
        "temp_inset": 10,
        # Vertical offsets from the bottom of the artwork
        "title_y": 8,
        "artist_y": 36,
        "year_y": 58,
        # Vertical offset from the bottom of the display
        "temp_y": 20,
        # Size of the border around the artwork, in pixels
        "border": 4
    },
    "strings": {
        "idle": "JELLYHAT IDLE"
    }
}