import time

from typing import NamedTuple

class ScreenState(NamedTuple):
    was_blanked: bool
    was_dimmed: bool
    is_blanked: bool
    is_dimmed: bool

class ScreenStateManager:
    """
    Manages the state related to screen blanking and dimming based on activity.
    """
    def __init__(self, blank_minutes: int, dim_minutes: int):
        """
        Initializes the ScreenStateManager.

        Args:
            blank_minutes: The number of minutes of inactivity before the screen blanks.  If 0 or less, blanking is disabled.
            dim_minutes: The number of minutes of inactivity before the screen dims. If 0 or less, dimming is disabled.  If greater than blank_minutes, dimming will not be used
        """
        self._use_blank = blank_minutes > 0
        self._use_dim = dim_minutes > 0 and dim_minutes < blank_minutes
        self._last_playing_time = time.time()
        self._blank_interval_seconds = blank_minutes * 60
        self._dim_interval_seconds = dim_minutes * 60
        self._is_blanked = False
        self._is_dimmed = False

    def update_activity(self, has_active_item: bool, is_item_paused: bool) -> ScreenState:
        """
        Updates the internal state based on current activity.
        This method should be called at the beginning of each main loop iteration.

        Args:
            has_active_item: True if there is an active Jellyfin item playing or paused.
            is_item_paused: True if the active Jellyfin item is currently paused.
        """
        was_blanked = self._is_blanked
        was_dimmed = self._is_dimmed
        if has_active_item and not is_item_paused:
            self._last_playing_time = time.time()

        elapsed = time.time() - self._last_playing_time
        self._is_blanked = self._use_blank and elapsed > self._blank_interval_seconds
        self._is_dimmed = self._use_dim and elapsed > self._dim_interval_seconds
        return ScreenState(
            was_blanked = was_blanked,
            was_dimmed = was_dimmed,
            is_blanked = self._is_blanked,
            is_dimmed = self._is_dimmed
        )
