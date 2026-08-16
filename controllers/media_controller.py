"""
media_controller.py
-------------------
Media / volume controller for AI Virtual Mouse Pro v3.0.

Uses:
    pynput -> real media key events

Responsibilities:
- Volume up
- Volume down
- Mute toggle
- Play / pause
- Next track
- Previous track
- Safe key release

This class does NOT detect gestures.
GestureDetector/GestureManager decide what should happen.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from pynput.keyboard import Controller, Key, KeyCode


class MediaController:
    """
    Controls system media playback and volume using pynput.

    Media keys are resolved once at construction time. When the
    installed pynput build does not expose a named media Key, a
    Windows virtual-key code is used instead.
    """

    # ============================================================
    # WINDOWS VIRTUAL KEY CODES (fallback)
    # ============================================================

    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    VK_MEDIA_NEXT = 0xB0
    VK_MEDIA_PREV = 0xB1
    VK_MEDIA_PLAY_PAUSE = 0xB3

    def __init__(
        self,
        action_cooldown: float = 0.30,
        volume_cooldown: float = 0.12,
        volume_step: int = 1,
    ):

        # ------------------------------------------------------
        # pynput keyboard controller
        # ------------------------------------------------------

        self.keyboard = Controller()

        # ------------------------------------------------------
        # Configuration
        # ------------------------------------------------------

        self.action_cooldown = max(
            0.0,
            float(action_cooldown),
        )

        self.volume_cooldown = max(
            0.0,
            float(volume_cooldown),
        )

        self.volume_step = max(
            1,
            min(5, int(volume_step)),
        )

        # ------------------------------------------------------
        # Resolved media keys
        # ------------------------------------------------------

        self.key_volume_up = self._resolve_key(
            "media_volume_up",
            self.VK_VOLUME_UP,
        )

        self.key_volume_down = self._resolve_key(
            "media_volume_down",
            self.VK_VOLUME_DOWN,
        )

        self.key_volume_mute = self._resolve_key(
            "media_volume_mute",
            self.VK_VOLUME_MUTE,
        )

        self.key_play_pause = self._resolve_key(
            "media_play_pause",
            self.VK_MEDIA_PLAY_PAUSE,
        )

        self.key_next = self._resolve_key(
            "media_next",
            self.VK_MEDIA_NEXT,
        )

        self.key_previous = self._resolve_key(
            "media_previous",
            self.VK_MEDIA_PREV,
        )

        # ------------------------------------------------------
        # Timing state
        # ------------------------------------------------------

        self.last_action_time = 0.0
        self.last_volume_time = 0.0

        # ------------------------------------------------------
        # Mute state (best effort, toggle based)
        # ------------------------------------------------------

        self.muted = False

    # ==========================================================
    # KEY RESOLUTION
    # ==========================================================

    @staticmethod
    def _resolve_key(
        name: str,
        virtual_key: int,
    ) -> Any:
        """
        Return the named pynput media Key when available,
        otherwise a Windows virtual-key KeyCode.
        """

        key = getattr(
            Key,
            name,
            None,
        )

        if key is not None:
            return key

        try:

            return KeyCode.from_vk(
                virtual_key
            )

        except Exception as e:

            print(
                f"[MediaController] Key resolve failed for {name}: {e}"
            )

            return None

    # ==========================================================
    # KEY TAP
    # ==========================================================

    def _tap(
        self,
        key: Any,
        repeat: int = 1,
    ) -> bool:
        """
        Press and release a media key.

        Returns True when the key was sent.
        """

        if key is None:
            return False

        try:

            for _ in range(max(1, int(repeat))):

                self.keyboard.press(
                    key
                )

                self.keyboard.release(
                    key
                )

            return True

        except Exception as e:

            print(
                f"[MediaController] Tap failed: {e}"
            )

            return False

    # ==========================================================
    # COOLDOWNS
    # ==========================================================

    def _action_allowed(self) -> bool:

        now = time.monotonic()

        return (
            now - self.last_action_time
            >= self.action_cooldown
        )

    def _volume_allowed(self) -> bool:

        now = time.monotonic()

        return (
            now - self.last_volume_time
            >= self.volume_cooldown
        )

    # ==========================================================
    # VOLUME
    # ==========================================================

    def volume_up(
        self,
        steps: Optional[int] = None,
    ) -> bool:
        """
        Raise system volume.

        Repeats are rate limited by volume_cooldown so a held
        gesture ramps smoothly instead of jumping.
        """

        if not self._volume_allowed():
            return False

        sent = self._tap(
            self.key_volume_up,
            self.volume_step
            if steps is None
            else steps,
        )

        if sent:

            self.last_volume_time = (
                time.monotonic()
            )

            self.muted = False

        return sent

    def volume_down(
        self,
        steps: Optional[int] = None,
    ) -> bool:
        """
        Lower system volume.
        """

        if not self._volume_allowed():
            return False

        sent = self._tap(
            self.key_volume_down,
            self.volume_step
            if steps is None
            else steps,
        )

        if sent:

            self.last_volume_time = (
                time.monotonic()
            )

        return sent

    def toggle_mute(self) -> bool:
        """
        Toggle system mute.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_volume_mute
        )

        if sent:

            self.last_action_time = (
                time.monotonic()
            )

            self.muted = not self.muted

        return sent

    # ==========================================================
    # PLAYBACK
    # ==========================================================

    def play_pause(self) -> bool:
        """
        Toggle playback of the active media session.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_play_pause
        )

        if sent:

            self.last_action_time = (
                time.monotonic()
            )

        return sent

    def next_track(self) -> bool:
        """
        Skip to the next track.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_next
        )

        if sent:

            self.last_action_time = (
                time.monotonic()
            )

        return sent

    def previous_track(self) -> bool:
        """
        Return to the previous track.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_previous
        )

        if sent:

            self.last_action_time = (
                time.monotonic()
            )

        return sent

    # ==========================================================
    # EVENT DISPATCH
    # ==========================================================

    def handle_event(
        self,
        event: str,
    ) -> bool:
        """
        Execute a media event name produced by GestureManager.

        Returns True when an action was performed.
        """

        if not event:
            return False

        if event == "VOLUME_UP":
            return self.volume_up()

        if event == "VOLUME_DOWN":
            return self.volume_down()

        if event == "MUTE":
            return self.toggle_mute()

        if event == "PLAY_PAUSE":
            return self.play_pause()

        if event == "NEXT_TRACK":
            return self.next_track()

        if event == "PREV_TRACK":
            return self.previous_track()

        return False

    # ==========================================================
    # STATUS
    # ==========================================================

    def is_muted(self) -> bool:
        """Return last known mute state."""

        return self.muted

    # ==========================================================
    # EMERGENCY RELEASE
    # ==========================================================

    def release_all(self):
        """
        Safely release any held media keys.

        Always call this when:
        - application stops
        - camera disconnects
        - an exception occurs
        """

        for key in (
            self.key_volume_up,
            self.key_volume_down,
            self.key_volume_mute,
            self.key_play_pause,
            self.key_next,
            self.key_previous,
        ):

            if key is None:
                continue

            try:

                self.keyboard.release(
                    key
                )

            except Exception:
                pass

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset controller timing state.
        """

        self.release_all()

        self.last_action_time = 0.0
        self.last_volume_time = 0.0

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Safely shut down the media controller.
        """

        self.release_all()
