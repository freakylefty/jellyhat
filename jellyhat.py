#!/usr/bin/env python3

import argparse
import sys
import time
import traceback
import os
from PIL import Image

from config import THEME, JELLYFIN_URL, JELLYFIN_API_KEY
from jellyfin_client import JellyfinClient
from hardware import DisplayManager

def get_args():
    parser = argparse.ArgumentParser(description="JellyHat")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Refresh interval (s)")
    parser.add_argument("-t", "--threshold", type=float, default=70.0, help="Temp threshold for LED")
    parser.add_argument("-r", "--rotate", action="store_true", help="Rotate 180°")
    parser.add_argument("-b", "--blank", type=int, default=10, help="Minutes before blanking screen")
    parser.add_argument("-H", "--hide-temp", action="store_true", help="Hide temp text")
    parser.add_argument("-d", "--debug", action="store_true", help="More verbose error messages")
    return parser.parse_args()

def main():
    if not JELLYFIN_URL or not JELLYFIN_API_KEY:
        print("Missing JELLYFIN_URL or JELLYFIN_API_KEY in .env")
        sys.exit(1)
        
    args = get_args()
    client = JellyfinClient(JELLYFIN_URL, JELLYFIN_API_KEY)
    
    try:
        dm = DisplayManager(rotate=args.rotate)
    except RuntimeError as e:
        print(f"Hardware Error: {e}")
        sys.exit(1)

    placeholder_path = os.path.join(os.path.dirname(__file__), "placeholder.png")
    placeholder_img = Image.open(placeholder_path).convert("RGB") if os.path.exists(placeholder_path) else None

    current_item_id = None
    cached_art = None
    last_active_time = time.time()
    is_blanked = False

    try:
        while True:
            active_item, err = client.get_active_item()
            temp = dm.get_system_temp()
            is_hot = temp >= args.threshold if temp is not None else False
            
            # --- BLANKING LOGIC ---
            if active_item:
                last_active_time = time.time()
                if is_blanked:
                    is_blanked = False
            
            if not active_item and (time.time() - last_active_time) > (args.blank * 60):
                if not is_blanked:
                    is_blanked = True
                    dm.clear()
                    dm.set_led(THEME["colors"]["temp_led_off"])
                    dm.update()
                time.sleep(args.interval)
                continue

            # --- RENDERING ---
            dm.clear()
            dm.set_led(THEME["colors"]["temp_led_hot"] if is_hot else THEME["colors"]["temp_led_normal"])

            if err:
                dm.draw_text(err, (dm.width//2 - 40, dm.height//2), "status", THEME["colors"]["status_err"])
            elif active_item:
                item_id = active_item.get('ParentLogoItemId') or active_item.get('Id')
                if item_id != current_item_id:
                    current_item_id = item_id
                    cached_art = client.get_artwork(item_id, THEME["layout"]["art_max_height"], THEME["layout"]["art_max_width"])
                    if not cached_art:
                        cached_art = placeholder_img

                dm.paste_image(cached_art)
                
                title = dm.truncate_text(active_item.get("Name", "Unknown"), "title", dm.width - 20)
                artist = dm.truncate_text(active_item.get("Artists", ["Unknown"])[0], "meta", dm.width - 20)
                
                dm.draw_text(title, (THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["title_y"]), "title", THEME["colors"]["text_main"])
                dm.draw_text(artist, (THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["artist_y"]), "meta", THEME["colors"]["text_dim"])
            else:
                current_item_id = None
                dm.draw_text(THEME["strings"]["idle"], (dm.width//2 - 60, dm.height//2), "status", THEME["colors"]["status_idle"])

            if not args.hide_temp and temp is not None:
                color = THEME["colors"]["temp_text_hot"] if is_hot else THEME["colors"]["temp_text_normal"]
                dm.draw_text(f"{temp:.1f}C", (THEME["layout"]["text_x"], THEME["layout"]["art_max_height"] + THEME["layout"]["temp_y"]), "meta", color)

            dm.update()
            time.sleep(args.interval)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            traceback.print_exc()
    finally:
        if 'dm' in locals():
            dm.set_led(THEME["colors"]["temp_led_off"])

if __name__ == "__main__":
    main()