"""
presentation_controller.py
--------------------------
Slide / presentation controller for AI Virtual Mouse Pro v3.0.

Uses:
    pynput -> real keyboard events

Responsibilities:
- Next slide
- Previous slide
- Start presentation
- End presentation
- Blank screen toggle
- Safe key release

Works with any presenter that follows the standard shortcuts
(PowerPoint, Google Slides, LibreOffice Impress, PDF viewers).

This class does NOT detect gestures.
GestureDetector/GestureManager decide what should happen.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from pynput.keyboard import Controller, Key


class PresentationController:
    """
    Drives slide navigation using pynput keyboard events.

    Navigation uses the arrow keys by default because they are the
    most widely supported. Page Up / Page Down can be selected
    instead for presenters that ignore arrows.
    """

    def __init__(
        self,
        action_cooldown: float = 0.60,
        use_page_keys: bool = False,
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

        self.use_page_keys = bool(
            use_page_keys
        )

        # ------------------------------------------------------
        # Navigation keys
        # ------------------------------------------------------

        self.key_next = (
            Key.page_down
            if self.use_page_keys
            else Key.right
        )

        self.key_previous = (
            Key.page_up
            if self.use_page_keys
            else Key.left
        )

        # ------------------------------------------------------
        # Timing state
        # ------------------------------------------------------

        self.last_action_time = 0.0

        # ------------------------------------------------------
        # Presentation state (best effort, toggle based)
        # ------------------------------------------------------

        self.presenting = False

        self.blanked = False

    # ==========================================================
    # KEY TAP
    # ==========================================================

    def _tap(
        self,
        key: Any,
    ) -> bool:
        """
        Press and release a key.

        Returns True when the key was sent.
        """

        if key is None:
            return False

        try:

            self.keyboard.press(
                key
            )

            self.keyboard.release(
                key
            )

            return True

        except Exception as e:

            print(
                f"[PresentationController] Tap failed: {e}"
            )

            return False

    # ==========================================================
    # COOLDOWN
    # ==========================================================

    def _action_allowed(self) -> bool:

        now = time.monotonic()

        return (
            now - self.last_action_time
            >= self.action_cooldown
        )

    def _mark_action(self) -> None:

        self.last_action_time = (
            time.monotonic()
        )

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def next_slide(self) -> bool:
        """
        Advance to the next slide.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_next
        )

        if sent:

            self._mark_action()

        return sent

    def previous_slide(self) -> bool:
        """
        Return to the previous slide.
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            self.key_previous
        )

        if sent:

            self._mark_action()

        return sent

    # ==========================================================
    # PRESENTATION MODE
    # ==========================================================

    def start_presentation(self) -> bool:
        """
        Begin slideshow from the first slide (F5).
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            Key.f5
        )

        if sent:

            self._mark_action()

            self.presenting = True

        return sent

    def end_presentation(self) -> bool:
        """
        Exit slideshow (Esc).
        """

        if not self._action_allowed():
            return False

        sent = self._tap(
            Key.esc
        )

        if sent:

            self._mark_action()

            self.presenting = False

            self.blanked = False

        return sent

    def toggle_blank(self) -> bool:
        """
        Toggle a blank black screen (B).
        """

        if not self._action_allowed():
            return False

        try:

            self.keyboard.press("b")

            self.keyboard.release("b")

        except Exception as e:

            print(
                f"[PresentationController] Blank failed: {e}"
            )

            return False

        self._mark_action()

        self.blanked = not self.blanked

        return True

    # ==========================================================
    # EVENT DISPATCH
    # ==========================================================

    def handle_event(
        self,
        event: str,
    ) -> bool:
        """
        Execute a slide event name produced by GestureManager.

        Returns True when an action was performed.
        """

        if not event:
            return False

        if event == "NEXT_SLIDE":
            return self.next_slide()

        if event == "PREV_SLIDE":
            return self.previous_slide()

        if event == "START_PRESENTATION":
            return self.start_presentation()

        if event == "END_PRESENTATION":
            return self.end_presentation()

        if event == "BLANK_SCREEN":
            return self.toggle_blank()

        return False

    # ==========================================================
    # STATUS
    # ==========================================================

    def is_presenting(self) -> bool:
        """Return last known slideshow state."""

        return self.presenting

    # ==========================================================
    # EMERGENCY RELEASE
    # ==========================================================

    def release_all(self):
        """
        Safely release any held navigation keys.

        Always call this when:
        - application stops
        - camera disconnects
        - an exception occurs
        """

        for key in (
            self.key_next,
            self.key_previous,
            Key.f5,
            Key.esc,
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

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Safely shut down the presentation controller.
        """

        self.release_all()
