import logging
from PIL import ImageFont
from config import THEME, FONT
logger = logging.getLogger(__name__)

class TextHandler:
    """Centralized manager for fonts and text processing."""
    def __init__(self):
        self.fonts = self._load_fonts()

    def get_font(self, font_key):
        return self.fonts.get(font_key, self.fonts.get("status"))
    
    def get_font_size(self, font_key, text):
        font = self.get_font(font_key)
        bounds = font.getbbox(text)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        return (width, height)

    def truncate_text(self, text, font_key, max_width):
        font = self.get_font(font_key)
        if font.getlength(text) <= max_width:
            return text
        while len(text) > 0 and font.getlength(text + "...") > max_width:
            text = text[:-1]
        return text + "..." if text else "..."
    
    def fit_text(self, text, font_key, max_width, max_height):
        font = self.get_font(font_key)
        lines = []
        current_line = ""
        y = 0
        for word in text.split():
            new_text = current_line + word + " "
            width, height = self.get_font_size(font_key, new_text)
            if width <= max_width and y + height <= max_height:
                current_line += word + " "
            else:
                y += height
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(self.truncate_text(current_line.strip(), font_key, max_width))
        return lines
    
    def calculate_aligned_position(self, text, font_key, position, align):
        font = self.get_font(font_key)
        text_width = font.getlength(text)
        if align == "right":
            return (position[0] - text_width, position[1])
        elif align in ("center", "centre"):
            return (position[0] - text_width // 2, position[1])
        return position

    def _load_fonts(self):
        font_path = FONT
        logger.info(f"Loading fonts from {font_path}")
        try:
            return {
                "title": ImageFont.truetype(font_path, THEME["fonts"]["size_title"]),
                "meta": ImageFont.truetype(font_path, THEME["fonts"]["size_meta"]),
                "meta_sm": ImageFont.truetype(font_path, THEME["fonts"]["size_meta_sm"]),
                "status": ImageFont.truetype(font_path, THEME["fonts"]["size_status"])
            }
        except IOError:
            logger.warning(f"Could not load font at {font_path}, falling back to default.")
            default = ImageFont.load_default()
            return {"title": default, "meta": default, "meta_sm": default, "status": default}

# Singleton instance to be imported by other modules
text_handler = TextHandler()