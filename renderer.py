import os
import logging
from PIL import Image
from config import THEME, PLACEHOLDER

logger = logging.getLogger(__name__)

class JellyRenderer:
    """Handles the visual layout and rendering for JellyHat."""
    
    def __init__(self, display_manager):
        self.dm = display_manager
        self.width = display_manager.width
        self.height = display_manager.height
        self.placeholder_img = self._load_placeholder()
        self.assets = {
            "play": self._load_asset("play.png", size=(50, 50)),
            "pause": self._load_asset("pause.png", size=(50, 50)),
            "warning": self._load_asset("warning.png"),
            "stop": self._load_asset("stop.png")
        }

    def clear(self, is_hot=False):
        """Clears the display and sets the LED based on thermal status."""
        self.dm.clear()
        led_color = THEME["colors"]["temp_led_hot"] if is_hot else THEME["colors"]["temp_led_normal"]
        self.dm.set_led(led_color)

    def blank(self):
        """Completely blanks the display and LEDs."""
        self.dm.clear()
        self.dm.set_brightness(0)
        self.dm.set_led(THEME["colors"]["temp_led_off"])
        self.dm.update()

    def draw_error(self, message):
        """Renders an error message centered on screen."""
        self._draw_icon("warning", (self.width // 2 - 10, self.height // 2 - 24))
        self.dm.draw_text(message, (self.width // 2, self.height // 2), "status", THEME["colors"]["status_err"], align="center")
        self.dm.set_brightness(1.0)

    def draw_idle(self):
        """Renders the idle screen state."""
        self._draw_icon("stop", (self.width // 2 - 10, self.height // 2 - 24))
        self.dm.draw_text(THEME["strings"]["idle"], (self.width // 2, self.height // 2), "status", THEME["colors"]["status_idle"], align="center")
        self.dm.set_brightness(1.0)

    def get_bordered_artwork(self, artwork):
        """Adds a border around the artwork, with colour based on the art."""
        if not artwork:
            return self.placeholder_img
        border_size = THEME["layout"]["art"]["border"]
        border = artwork.resize((1, 1), Image.BOX)
        bordered_art = Image.new("RGBA", (artwork.width + (border_size * 2), artwork.height + (border_size * 2)), border.getpixel((0, 0)))
        self.dm.paste_image(image=artwork, target=bordered_art, position=(border_size, border_size))
        return bordered_art

    def draw_playing(self, active_item, artwork, dimmed=False):
        """Renders the 'Now Playing' screen with artwork and metadata."""

        # Render Artwork
        self.dm.paste_image(image=artwork, position=(0, 0))

        is_paused = active_item.get("IsPaused", False)
        self._draw_icon("pause" if is_paused else "play", (THEME["layout"]["icon"]["left"], THEME["layout"]["icon"]["top"]))

        match active_item.get("Type"):
            case "Movie" | "Episode" | "Video":
                self._render_video(active_item.get('Name', 'Unknown'), active_item.get("ProductionYear", ""))
            case "AudioBook":
                 self._render_book(active_item.get('Name', 'Unknown'))
            case "Audio":
                if active_item.get("ProviderIds", {}).get("BookItemId"):
                    self._render_book(active_item.get('Name', 'Unknown'))
                else:
                    self._render_music(active_item.get('Name', 'Unknown'), active_item.get("Artists", ["Unknown"]), active_item.get("Album", ""), active_item.get("ProductionYear", ""))
            case _:
                self._render_generic(active_item.get('Name', 'Unknown'))
                
        self.dm.set_brightness(1 if not dimmed else THEME["colors"]["screen_dim"])

    def draw_temp(self, temp, is_hot):
        """Renders the system temperature."""
        color = THEME["colors"]["temp_text_hot"] if is_hot else THEME["colors"]["temp_text_normal"]
        self.dm.draw_text(f"{temp:.1f}C", (self.width - THEME["layout"]["temp"]["right"], self.height - THEME["layout"]["temp"]["bottom"]), "meta", color, align="right")

    def update(self):
        """Triggers the hardware display refresh."""
        self.dm.update()

    def _render_video(self, title, year):
        # Render Title
        title_left = THEME["layout"]["video"]["left"]
        title_right = THEME["layout"]["video"]["right"]
        title = self.dm.truncate_text(title, "meta", self.width - (title_left + title_right))
        self.dm.draw_text(
            title, 
            (title_left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["video"]["title_top"]), 
            "meta", 
            THEME["colors"]["text_main"]
        )

        # Render Year 
        if year:
            self.dm.draw_text(
            f"{year}",
            (title_left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["video"]["year_top"]), 
            "meta", 
            THEME["colors"]["text_dim"]
        )
        
    def _render_music(self, title, artists, album, year):
        # Render Title
        left = THEME["layout"]["music"]["left"]
        right = THEME["layout"]["music"]["right"]
        max_width = self.width - (left + right)
        title = self.dm.truncate_text(title, "title", max_width)
        self.dm.draw_text(
            title, 
            (left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["music"]["title_top"]), 
            "title", 
            THEME["colors"]["text_main"]
        )
       
        # Render Artist
        artist_text = artists[0] if artists else "Unknown"
        artist = self.dm.truncate_text(artist_text, "meta", max_width)
        
        self.dm.draw_text(
            artist, 
            (left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["music"]["artist_top"]), 
            "meta", 
            THEME["colors"]["text_dim"]
        )

        # Render Album and Year
        year = f"({year})" if album else year
        if self.draw_temp:
            max_width -= 50 # Make room for temp display
        album_text = self.dm.truncate_text(f"{album} {year}".strip(), "meta_sm", max_width)

        if album_text:
            self.dm.draw_text(
            album_text, 
            (left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["music"]["year_top"]), 
            "meta_sm", 
            THEME["colors"]["text_dim"]
        )

    def _render_book(self, title):
        left = THEME["layout"]["generic"]["left"]
        right = THEME["layout"]["generic"]["right"]
        max_width = self.width - (left + right)
        title = self.dm.truncate_text(title, "title", max_width)
        self.dm.draw_text(
            title, 
            (left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["generic"]["title_top"]), 
            "meta", 
            THEME["colors"]["text_main"]
        )

    def _render_generic(self, title):
        left = THEME["layout"]["generic"]["left"]
        right = THEME["layout"]["generic"]["right"]
        max_width = self.width - (left + right)
        title = self.dm.truncate_text(title, "title", max_width)
        self.dm.draw_text(
            title, 
            (left, THEME["layout"]["art"]["max_height"] + THEME["layout"]["generic"]["title_top"]), 
            "meta", 
            THEME["colors"]["text_main"]
        )

    def _draw_icon(self, icon_key, position):
        """Draws a predefined icon at the specified position."""
        icon = self.assets.get(icon_key)
        if icon:
            self.dm.paste_image(image=icon, position=position)

    def _load_asset(self, filename, size=(20, 20)):
        """Loads and resizes a UI asset from the assets folder."""
        asset_path = os.path.join(os.path.dirname(__file__), "assets", filename)
        try:
            if os.path.exists(asset_path):
                img = Image.open(asset_path).convert("RGBA")
                return img.resize(size, Image.NEAREST)
        except Exception as e:
            logger.warning(f"Could not load asset {filename}: {e}")
        return Image.new("RGBA", size, (0, 0, 0, 0))
    
    def _get_scaled_size(self, width, height, max_width, max_height):
        """Calculates the scaled size for an image while maintaining aspect ratio."""
        aspect_ratio = width / height
        new_width = max_width
        new_height = int(new_width / aspect_ratio)
        if new_height > max_height:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)
        return new_width, new_height

    def _load_placeholder(self):
        """Loads and prepares the placeholder artwork."""
        max_width = THEME["layout"]["art"]["max_width"]
        max_height = THEME["layout"]["art"]["max_height"]

        placeholder_path = PLACEHOLDER
        if os.path.exists(placeholder_path):
            try:
                logger.info(f"Loading placeholder from {placeholder_path}")
                img = Image.open(placeholder_path).convert("RGB")
                width, height = self._get_scaled_size(img.width, img.height, max_width, max_height)
                img = img.resize((width, height), Image.LANCZOS)
                return img
            except Exception:
                logger.error("Failed to process placeholder image", exc_info=True)
        logger.warning("Placeholder image not found or failed to load. Using blank image.")
        return Image.new("RGBA", (max_width, max_height), THEME["colors"]["background"])