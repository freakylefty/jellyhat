import os
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
from config import THEME

class DisplayManager:
    def __init__(self, rotate=False):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.rotate = rotate
        self.buffer = Image.new("RGB", (self.width, self.height), THEME["colors"]["background"])
        self.draw = ImageDraw.Draw(self.buffer)
        self.dh = DisplayHATMini(self.buffer)
        self.fonts = self._load_fonts()
        self._temp_enabled = True

    def _load_fonts(self):
        font_path = os.path.join(os.path.dirname(__file__), THEME["fonts"]["path"])
        try:
            return {
                "title": ImageFont.truetype(font_path, THEME["fonts"]["size_title"]),
                "meta": ImageFont.truetype(font_path, THEME["fonts"]["size_meta"]),
                "status": ImageFont.truetype(font_path, THEME["fonts"]["size_status"])
            }
        except IOError:
            default = ImageFont.load_default()
            return {"title": default, "meta": default, "status": default}

    def truncate_text(self, text, font_key, max_width):
        font = self.fonts[font_key]
        if font.getsize(text)[0] <= max_width:
            return text
        while len(text) > 0 and font.getsize(text)[0] > max_width:
            text = text[:-1]
        return text + "..." if text else "..."

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), THEME["colors"]["background"])

    def set_led(self, color_tuple):
        try:
            r, g, b = [c / 255.0 for c in color_tuple]
            self.dh.set_led(r, g, b)
        except Exception:
            pass

    def paste_image(self, image, position=(0, 0)):
        if image:
            self.buffer.paste(image, position)

    def draw_text(self, text, position, font_key, color):
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
            self._temp_enabled = False
            return None