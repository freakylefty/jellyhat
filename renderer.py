import os
from PIL import Image
from config import THEME

class JellyRenderer:
    """Handles the visual layout and rendering for JellyHat."""
    
    def __init__(self, display_manager):
        self.dm = display_manager
        self.width = display_manager.width
        self.height = display_manager.height
        self.placeholder_img = self._load_placeholder()

    def _load_placeholder(self):
        """Loads and prepares the placeholder artwork."""
        size = min(THEME["layout"]["art_max_height"], THEME["layout"]["art_max_width"])
        placeholder_path = os.path.join(os.path.dirname(__file__), "placeholder.jpg")
        if os.path.exists(placeholder_path):
            try:
                img = Image.open(placeholder_path).convert("RGB")
                return img.resize((size, size), Image.ANTIALIAS)
            except Exception:
                pass
        print("Warning: Placeholder image not found or failed to load. Using blank image.")
        return Image.new("RGB", (size, size), THEME["colors"]["background"])

    def clear(self, is_hot=False):
        """Clears the display and sets the LED based on thermal status."""
        self.dm.clear()
        led_color = THEME["colors"]["temp_led_hot"] if is_hot else THEME["colors"]["temp_led_normal"]
        self.dm.set_led(led_color)

    def blank(self):
        """Completely blanks the display and LEDs."""
        self.dm.clear()
        self.dm.set_led(THEME["colors"]["temp_led_off"])
        self.dm.update()

    def draw_error(self, message):
        """Renders an error message centered on screen."""
        self.dm.draw_text(message, (self.width // 2, self.height // 2), "status", THEME["colors"]["status_err"], align="center")

    def draw_idle(self):
        """Renders the idle screen state."""
        self.dm.draw_text(THEME["strings"]["idle"], (self.width // 2, self.height // 2), "status", THEME["colors"]["status_idle"], align="center")

    def get_bordered_artwork(self, artwork):
        """Adds a border around the artwork, with colour based on the art."""
        if not artwork:
            return self.placeholder_img
        border_size = THEME["layout"]["border"]
        border = artwork.resize((1, 1), Image.BOX)
        bordered_art = Image.new("RGB", (artwork.width + (border_size * 2), artwork.height + (border_size * 2)), border.getpixel((0, 0)))
        bordered_art.paste(artwork, (border_size, border_size))
        return bordered_art

    def draw_playing(self, active_item, artwork):
        """Renders the 'Now Playing' screen with artwork and metadata."""
        # Render Artwork
        self.dm.paste_image(artwork, (0, 0))

        # Render Title with Play/Pause status
        is_paused = active_item.get("IsPaused", False)
        symbol = THEME["strings"]["pause_symbol"] if is_paused else THEME["strings"]["play_symbol"]
        title_text = f"{symbol} {active_item.get('Name', 'Unknown')}"
        title = self.dm.truncate_text(title_text, "title", self.width - 20)
        
        self.dm.draw_text(
            title, 
            (THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["title_y"]), 
            "title", 
            THEME["colors"]["text_main"]
        )

        # Render Artist
        artists = active_item.get("Artists", ["Unknown"])
        artist_text = artists[0] if artists else "Unknown"
        artist = self.dm.truncate_text(artist_text, "meta", self.width - 20)
        
        self.dm.draw_text(
            artist, 
            (THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["artist_y"]), 
            "meta", 
            THEME["colors"]["text_dim"]
        )

    def draw_temp(self, temp, is_hot):
        """Renders the system temperature."""
        color = THEME["colors"]["temp_text_hot"] if is_hot else THEME["colors"]["temp_text_normal"]
        self.dm.draw_text(f"{temp:.1f}C", (self.width - THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["temp_y"]), "meta", color, align="right")

    def update(self):
        """Triggers the hardware display refresh."""
        self.dm.update()