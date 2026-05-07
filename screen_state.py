import time

class ScreenStateManager:
    """
    Manages the state related to screen blanking and dimming based on activity.
    """
    def __init__(self, blank_minutes: int, dim_minutes: int):
        """
        Initializes the ScreenStateManager.

        Args:
            blank_minutes: The number of minutes of inactivity before the screen blanks.  If 0 or less, blanking is disabled.
            dim_minutes: The number of minutes of paused playback before the screen dims. If 0 or less, dimming is disabled.
        """
        self.use_blank = blank_minutes > 0
        self.use_dim = dim_minutes > 0
        self._blank_interval_seconds = blank_minutes * 60
        self._dim_interval_seconds = dim_minutes * 60
        self._last_active_time = time.time()
        self._last_playing_time = time.time()
        self._is_blanked = False
        self._is_paused_state = False

    def update_activity(self, has_active_item: bool, is_item_paused: bool):
        """
        Updates the internal state based on current activity.
        This method should be called at the beginning of each main loop iteration.

        Args:
            has_active_item: True if there is an active Jellyfin item playing or paused.
            is_item_paused: True if the active Jellyfin item is currently paused.
        """
        if has_active_item:
            self._last_active_time = time.time()
            self._is_paused_state = is_item_paused
            # If playback resumes (not paused) or we just unblanked, reset playing time
            if not is_item_paused or self._is_blanked:
                self._last_playing_time = time.time()
            # If we were blanked and now there's an active item, implicitly unblank
            if self._is_blanked:
                self._is_blanked = False
        else:
            # No active item, so not paused in the context of an item
            self._is_paused_state = False

    def check_for_blanking_transition(self) -> bool:
        """
        Checks if the screen should transition to a blanked state.
        Returns True if the screen *just transitioned* to blanked state in this call.
        Returns False if not enabled, already blanked, or not yet time to blank.
        """
        if not self.use_blank:
            return False
        if not self._is_blanked and (time.time() - self._last_active_time) > self._blank_interval_seconds:
            self._is_blanked = True
            return True
        return False

    def is_currently_blanked(self) -> bool:
        """
        Returns True if the screen is currently in a blanked state.
        Returns False if blanking is not enabled or if the screen is currently active.
        """
        if not self.use_blank:
            return False
        return self._is_blanked

    def is_dim_needed(self) -> bool:
        """
        Returns True if the screen should be dimmed due to paused playback exceeding the dim interval.
        Returns False if dimming is not enabled, or if not currently in a paused state, or if the dim interval has not yet been exceeded.
        """
        if not self.use_dim:
            return False
        return self._is_paused_state and (time.time() - self._last_playing_time) > self._dim_interval_seconds
