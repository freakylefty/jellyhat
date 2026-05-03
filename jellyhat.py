#!/usr/bin/env python3

import argparse
import os
import requests
import sys
import time
import traceback
from displayhatmini import DisplayHATMini
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# --- THEME & UI CONFIGURATION ---
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
        "title_y": 4,
        "artist_y": 28,
        "temp_x": 10,
        "temp_y": 50,
    },
    "strings": {
        "idle": "JELLYHAT IDLE",
        "blanked": "[Screen Blanked - Energy Saving Mode]"
    }
}

# --- INITIALIZATION ---
load_dotenv()
URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
KEY = os.getenv("JELLYFIN_API_KEY")

def validate_env():
    missing = [var for var, val in {"JELLYFIN_URL": URL, "JELLYFIN_API_KEY": KEY}.items() if not val]
    if missing:
        print(f"Missing .env config: {', '.join(missing)}")
        sys.exit(1)

def truncate_text_by_width(text, font, max_width):
    if font.getsize(text)[0] <= max_width:
        return text
    
    ellipsis = "..."
    while len(text) > 0 and font.getsize(text)[0] > max_width:
        text = text[:-1]
        
    return text + ellipsis if text else ellipsis
    
def load_fonts():
    font_path = os.path.join(os.path.dirname(__file__), THEME["fonts"]["path"])
    try:
        title = ImageFont.truetype(font_path, THEME["fonts"]["size_title"])
        meta = ImageFont.truetype(font_path, THEME["fonts"]["size_meta"])
        status = ImageFont.truetype(font_path, THEME["fonts"]["size_status"])
        return title, meta, status
    except IOError:
        print(f"WARNING: Font file not found. Falling back to system default.")
        default = ImageFont.load_default()
        return default, default, default

def set_hat_led(dh, color_tuple):
    try:
        r, g, b = [c / 255.0 for c in color_tuple]
        dh.set_led(r, g, b)
    except Exception as e:
        print(f"Failed to set LED: {e}")
        
def get_args():
    parser = argparse.ArgumentParser(description="JellyHat")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Refresh interval (s)")
    parser.add_argument("-t", "--threshold", type=float, default=70.0, help="Temp threshold for LED")
    parser.add_argument("-r", "--rotate", action="store_true", help="Rotate 180°")
    parser.add_argument("-b", "--blank", type=int, default=10, help="Minutes before blanking screen")
    parser.add_argument("-H", "--hide-temp", action="store_true", help="Hide temp text")
    parser.add_argument("-d", "--debug", action="store_true", help="More verbose error messages")
    return parser.parse_args()

def fetch_jellyfin_sessions():
    try:
        r = requests.get(f"{URL}/Sessions?api_key={KEY}", timeout=3)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, f"ERR: {type(e).__name__}"

def main():
    validate_env()
    args = get_args()
    f_title, f_meta, f_status = load_fonts()
    
    # --- Init DisplayHat ---
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT
    buffer = Image.new("RGB", (width, height), THEME["colors"]["background"])
    draw = ImageDraw.Draw(buffer)

    try:
        dh = DisplayHATMini(buffer)
    except RuntimeError as e:
        print(f"Could not init DisplayHAT: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

    # --- Init layout calculations ---
    placeholder_path = os.path.join(os.path.dirname(__file__), "placeholder.png")
    art_width = THEME["layout"]["art_max_width"]
    art_height = THEME["layout"]["art_max_height"]
    art_size = min([art_width, art_height])
    textX = THEME["layout"]["text_x"]
    titleY = art_height + THEME["layout"]["title_y"]
    artistY = art_height + THEME["layout"]["artist_y"]
    
    # --- State tracking ---
    current_item_id = None
    cached_art = None
    last_active_time = time.time()
    is_blanked = False

    print(f"Welcome to JellyHat")
    if (args.debug):
        print(f"Interval: {args.interval}s")
        print(f"Temperature Threshold: {args.threshold}c")
        print(f"Rotate output: {args.rotate}")
        print(f"Timeout: {args.blank}m")
        print(f"Hide temparture text: {args.hide_temp}")

    try:
        while True:
            sessions, err = fetch_jellyfin_sessions()
            
            # --- CLEAR DISPLAY ---
            draw.rectangle((0, 0, width, height), THEME["colors"]["background"])
            
            # --- SESSION PRIORITY LOGIC ---
            active_session = None
            if sessions:
                # Prioritize playing over paused
                active_session = next((s for s in sessions if "NowPlayingItem" in s and not s.get("PlayState", {}).get("IsPaused", False)), None)
                if not active_session:
                    active_session = next((s for s in sessions if "NowPlayingItem" in s), None)

            active_item = active_session["NowPlayingItem"] if active_session else None
            
            # --- GET TEMPERATURE ---
            temp = 0.0
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = float(f.read()) / 1000.0
            except: pass
            is_hot = temp >= args.threshold
            temp_text_color = THEME["colors"]["temp_text_hot"] if is_hot else THEME["colors"]["temp_text_normal"]
            temp_led_color = THEME["colors"]["temp_led_hot"] if is_hot else THEME["colors"]["temp_led_normal"]                

            # --- BLANKING LOGIC ---
            if active_item:
                last_active_time = time.time()
                if is_blanked:
                    print("Activity detected. Waking screen...")
                    is_blanked = False
            
            if not active_item and (time.time() - last_active_time) > (args.blank * 60):
                if not is_blanked:
                    print(THEME["strings"]["blanked"])
                    is_blanked = True
                
                set_hat_led(dh, THEME["colors"]["temp_led_off"])
                dh.display()  # Push the cleared buffer to hardware
                time.sleep(args.interval)
                continue

            set_hat_led(dh, temp_led_color)

            # --- RENDERING ---
            
            if err:
                draw.text((width//2 - 40, height//2), err, font=f_status, fill=THEME["colors"]["status_err"])
            elif active_item:
                item_id = active_item.get('ParentLogoItemId') or active_item.get('Id')
                if item_id != current_item_id:
                    current_item_id = item_id
                    cached_art = None
                    image_attempts = [
                        ("Backdrop", f"{URL}/Items/{item_id}/Images/Backdrop?quality=96&maxHeight={art_height}&maxWidth={art_width}&api_key={KEY}"),
                        ("Primary", f"{URL}/Items/{item_id}/Images/Primary?quality=96&maxHeight={art_height}&maxWidth={art_width}&api_key={KEY}"),
                        ("Logo", f"{URL}/Items/{item_id}/Images/Logo?quality=96&maxHeight={art_height}&maxWidth={art_width}&api_key={KEY}")
                    ]

                    art_found = False
                    for label, img_url in image_attempts:
                        try:
                            r = requests.get(img_url, timeout=2)
                            if r.status_code == 200:
                                with Image.open(BytesIO(r.content)) as art_file:
                                    cached_art = art_file.convert("RGB")
                                art_found = True
                                break
                        except Exception:
                            continue

                    # Final fallback to local file if no URLs worked
                    if not art_found:
                        try:
                            if os.path.exists(placeholder_path):
                                with Image.open(placeholder_path) as art_file:
                                    cached_art = art_file.convert("RGB")
                        except:
                            continue

                if cached_art:
                    buffer.paste(cached_art, (0, 0))
                else:
                    draw.rectangle((10, 10, art_size-10, art_size-10), outline=THEME["colors"]["status_idle"])

                title = active_item.get("Name", "Unknown Track")
                artist = active_item.get("Artists", ["Unknown Artist"])[0]
                
                disp_title = truncate_text_by_width(title, f_title, width - (2 * textX))
                disp_artist = truncate_text_by_width(artist, f_meta, width - (2 * textX))

                draw.text((textX, titleY), disp_title, font=f_title, fill=THEME["colors"]["text_main"])
                draw.text((textX, artistY), disp_artist, font=f_meta, fill=THEME["colors"]["text_dim"])
            else:
                current_item_id = None
                cached_art = None
                draw.text((width//2 - 60, height//2), THEME["strings"]["idle"], font=f_status, fill=THEME["colors"]["status_idle"])

            if not args.hide_temp:
                tempY = art_height + THEME["layout"]["temp_y"]
                draw.text((textX, tempY), f"{temp:.1f}C", font=f_meta, fill=temp_text_color)

            if args.rotate:
                rotated_snapshot = buffer.rotate(180)
                buffer.paste(rotated_snapshot, (0, 0))
            dh.display()
            time.sleep(args.interval)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            traceback.print_exc()
    finally:
        # Second layer of protection: 
        # Attempt to clear hardware only if the object exists 
        # and the hardware bus is still responsive.
        if 'dh' in locals():
            try:
                set_hat_led(dh, THEME["colors"]["temp_led_off"])
            except Exception:
                # If the HAT is unplugged or the bus crashed, 
                # we just want to exit silently now.
                print("Warning: Could not clear hardware LED (HAT disconnected or bus error).")
                if args.debug:
                    traceback.print_exc()

if __name__ == "__main__":
    main()