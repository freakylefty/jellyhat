#!/usr/bin/env python3

import argparse
import logging
import signal
import sys
import time

from config import THEME, JELLYFIN_URL, JELLYFIN_API_KEY
from jellyfin_client import JellyfinClient
from hardware import DisplayManager
from renderer import JellyRenderer
from screen_state import ScreenStateManager

logger = logging.getLogger(__name__)

def teardown(dm):
    if dm:
        logger.info("Cleaning up hardware and exiting.")
        dm.set_led(THEME["colors"]["temp_led_off"])
        dm.set_brightness(1)
        dm.clear()
        dm.update()
    sys.exit(0)

def get_args():
    parser = argparse.ArgumentParser(description="JellyHat")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Refresh interval (s)")
    parser.add_argument("-t", "--threshold", type=float, default=70.0, help="Temperature threshold for LED")
    parser.add_argument("-r", "--rotate", action="store_true", help="Rotate the Display HAT output by 180°")
    parser.add_argument("-b", "--blank", type=int, default=10, help="Minutes before blanking screen. Set to 0 to disable blanking.")
    parser.add_argument("-d", "--dim", type=int, default=2, help="Minutes before dimming screen. Set to 0 to disable dimming.")
    parser.add_argument("-H", "--hide-temp", action="store_true", help="Hide temp text")
    parser.add_argument("-l", "--log-level", type=str, choices=["debug", "info", "warning", "error"], default="warning", help="Set the logging level")

    return parser.parse_args()

def main():
    args = get_args()

    log_level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    if not JELLYFIN_URL or not JELLYFIN_API_KEY:
        logger.fatal("Missing JELLYFIN_URL or JELLYFIN_API_KEY in .env")
        sys.exit(1)
        
    client = JellyfinClient(JELLYFIN_URL, JELLYFIN_API_KEY)
    
    try:
        dm = DisplayManager(rotate=args.rotate)
        renderer = JellyRenderer(dm)
        signal.signal(signal.SIGINT, lambda sig, frame: teardown(dm))
        signal.signal(signal.SIGTERM, lambda sig, frame: teardown(dm))
    except RuntimeError as e:
        logger.fatal(f"Hardware Error: {e}", exc_info=True)
        sys.exit(1)

    current_item_id = None
    cached_art = None
    screen_state_manager = ScreenStateManager(args.blank, args.dim)

    try:
        while True:
            active_item, err = client.get_active_item()
            temp = dm.get_system_temp()
            is_hot = temp >= args.threshold if temp is not None else False
            
            is_item_paused = active_item.get("IsPaused", False) if active_item else False
            screen_state = screen_state_manager.update_activity(bool(active_item), is_item_paused)
            
            # --- Blanking ---
            # If only just blanked this frame, blank the DisplayHAT
            # If in blanked state then wait and resume the main loop
            if screen_state.is_blanked:
                if not screen_state.was_blanked:
                    renderer.blank()
                time.sleep(args.interval)
                continue

            # --- RENDERING ---
            renderer.clear(is_hot=is_hot)

            if err:
                renderer.draw_error(err)
            elif active_item:
                item_id = active_item.get('Id')
                if item_id != current_item_id:
                    current_item_id = item_id
                    cached_art = client.get_artwork(item_id, THEME["layout"]["art"]["max_height"], THEME["layout"]["art"]["max_width"])
                    if (not cached_art):
                        cached_art = client.get_artwork(active_item.get('ParentId'), THEME["layout"]["art"]["max_height"], THEME["layout"]["art"]["max_width"])
                    
                    cached_art = renderer.get_bordered_artwork(cached_art)

                renderer.draw_playing(active_item, cached_art, dimmed=screen_state.is_dimmed)
            else:
                current_item_id = None
                renderer.draw_idle()

            if not args.hide_temp and temp is not None:
                renderer.draw_temp(temp, is_hot)

            renderer.update()
            time.sleep(args.interval)
            
    except Exception as e:
        logger.fatal(f"Error in main loop: {e}", exc_info=True)
    finally:
        teardown(dm)

if __name__ == "__main__":
    main()