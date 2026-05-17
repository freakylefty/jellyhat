import logging
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
from config import THEME, FONT
from text_util import text_handler

logger = logging.getLogger(__name__)

class DisplayManager:
    def __init__(self, rotate=False):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.rotate = rotate
        self.buffer = Image.new("RGBA", (self.width, self.height), THEME["colors"]["background"])
        self.draw = ImageDraw.Draw(self.buffer, "RGBA")
        self.dh = DisplayHATMini(self.buffer, backlight_pwm=True)
        self._temp_enabled = True
        self._led_enabled = True
        self._backlight_enabled = True

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
        font = text_handler.get_font(font_key)
        pos = text_handler.calculate_aligned_position(text, font_key, position, align)
        self.draw.text(pos, text, font=font, fill=color)
        height = text_handler.get_font_size(font_key, text)[1]
        return position[1] + height

    def draw_texts(self, lines, position, font_key, color, align="left"):
        font = text_handler.get_font(font_key)
        for line in lines:
            new_top = self.draw_text(line, position, font_key, color, align)
            position = (position[0], new_top)
        return position[1]

    def update(self):
        if self.rotate:
            output = self.buffer.rotate(180)
            self.buffer.paste(output, (0, 0))
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

    def _get_mask(self, image):
        if image.mode == 'RGBA':
            return image.split()[3]  # Use alpha channel as mask
        return None