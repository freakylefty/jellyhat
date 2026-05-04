#!/usr/bin/env python3

import argparse
import sys
import time
import traceback

from config import THEME, JELLYFIN_URL, JELLYFIN_API_KEY
from jellyfin_client import JellyfinClient
from hardware import DisplayManager
from renderer import JellyRenderer

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
        renderer = JellyRenderer(dm)
    except RuntimeError as e:
        print(f"Hardware Error: {e}")
        sys.exit(1)

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
                    renderer.blank()
                time.sleep(args.interval)
                continue

            # --- RENDERING ---
            renderer.clear(is_hot=is_hot)

            if err:
                renderer.draw_error(err)
            elif active_item:
                item_id = active_item.get('ParentLogoItemId') or active_item.get('Id')
                if item_id != current_item_id:
                    current_item_id = item_id
                    cached_art = client.get_artwork(item_id, THEME["layout"]["art_max_height"], THEME["layout"]["art_max_width"])
                    cached_art = renderer.get_bordered_artwork(cached_art)

                renderer.draw_playing(active_item, cached_art)
            else:
                current_item_id = None
                renderer.draw_idle()

            if not args.hide_temp and temp is not None:
                renderer.draw_temp(temp, is_hot)

            renderer.update()
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