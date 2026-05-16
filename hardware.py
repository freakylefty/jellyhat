import logging
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
from config import THEME, FONT

logger = logging.getLogger(__name__)

class DisplayManager:
    def __init__(self, rotate=False):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.rotate = rotate
        self.buffer = Image.new("RGBA", (self.width, self.height), THEME["colors"]["background"])
        self.draw = ImageDraw.Draw(self.buffer, "RGBA")
        self.dh = DisplayHATMini(self.buffer, backlight_pwm=True)
        self.fonts = self._load_fonts()
        self._temp_enabled = True
        self._led_enabled = True
        self._backlight_enabled = True

    def truncate_text(self, text, font_key, max_width):
        font = self.fonts[font_key]
        if font.getlength(text) <= max_width:
            return text
        while len(text) > 0 and font.getlength(text + "...") > max_width:
            text = text[:-1]
        return text + "..." if text else "..."

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), THEME["colors"]["background"])

    def set_brightness(self, brightness):
        if not self._backlight_enabled:
            return
        try:
            # Clamp value between 0 and 1 just in case
            level = max(0.0, min(1.0, float(brightness)))
            self.dh.set_backlight(level)
        except AttributeError:
            logger.warning("Backlight control unavailable.")
            self._backlight_enabled = False
            pass

    def set_led(self, color_tuple):
        if not self._led_enabled:
            return
        try:
            r, g, b = [c / 255.0 for c in color_tuple]
            self.dh.set_led(r, g, b)
        except Exception:
            logger.warning("LED control unavailable.")
            self._led_enabled = False
            pass

    def paste_image(self, image, target=None, position=(0, 0)):
        if not image:
            return
        if target is None:
            target = self.buffer
        target.paste(image, position, self._get_mask(image))

    def draw_text(self, text, position, font_key, color, align="left"):
        if (align == "right"):
            font = self.fonts[font_key]
            text_width = font.getlength(text)
            position = (position[0] - text_width, position[1])
        elif (align == "center" or align == "centre"): # Yeah yeah, I'm British
            font = self.fonts[font_key]
            text_width = font.getlength(text)
            position = (position[0] - text_width // 2, position[1])
        self.draw.text(position, text, font=self.fonts[font_key], fill=color)

    def update(self):
        if self.rotate:
            output = self.buffer.rotate(180)
            self.buffer.paste(output, (0, 0))
            self.dh.display()
        else:
            self.dh.display()

    def get_system_temp(self):
        if not self._temp_enabled:
            return None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read()) / 1000.0
        except Exception:
            logger.warning("System temperature monitoring unavailable.")
            self._temp_enabled = False
            return None

    def _load_fonts(self):
        font_path = FONT
        logger.info(f"Loading font from {font_path}")
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
            return {"title": default, "meta": default, "status": default}
    
    def _get_mask(self, image):
        if image.mode == 'RGBA':
            return image.split()[3]  # Use alpha channel as mask
        return None