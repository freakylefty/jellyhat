import requests
from io import BytesIO
from PIL import Image

class JellyfinClient:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key

    def get_active_item(self):
        """Fetches sessions and returns the prioritized NowPlayingItem."""
        try:
            r = requests.get(f"{self.url}/Sessions?api_key={self.api_key}", timeout=3)
            r.raise_for_status()
            sessions = r.json()
            
            # Prioritize playing over paused
            active = next((s for s in sessions if "NowPlayingItem" in s and not s.get("PlayState", {}).get("IsPaused", False)), None)
            if not active:
                active = next((s for s in sessions if "NowPlayingItem" in s), None)
                
            return (active["NowPlayingItem"] if active else None), None
        except Exception as e:
            return None, f"ERR: {type(e).__name__}"

    def get_artwork(self, item_id, max_h, max_w):
        """Tries various image types from Jellyfin and returns a PIL Image."""
        image_types = ["Backdrop", "Primary", "Logo"]
        for img_type in image_types:
            img_url = f"{self.url}/Items/{item_id}/Images/{img_type}?quality=96&maxHeight={max_h}&maxWidth={max_w}&api_key={self.api_key}"
            try:
                r = requests.get(img_url, timeout=2)
                if r.status_code == 200:
                    return Image.open(BytesIO(r.content)).convert("RGB")
            except Exception:
                continue
        return None