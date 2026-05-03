import requests
from io import BytesIO
from PIL import Image

class JellyfinClient:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key

    def get_active_item(self):
        url = f"{self.url}/Sessions"
        headers = {
            "X-Emby-Token": self.api_key,
            "Accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            sessions = response.json()

            for session in sessions:
                if "NowPlayingItem" in session:
                    item_data = session["NowPlayingItem"]
                    play_state = session.get("PlayState", {})
                    item_data["IsPaused"] = play_state.get("IsPaused", False)
                    
                    return item_data, None
                    
            return None, None
        except Exception as e:
            return None, f"API Error: {str(e)}"

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