"""
mouse_controller.py
-------------------
Real-time mouse controller for AI Virtual Mouse Pro v3.0.

Uses:
    pynput -> real mouse movement and mouse events

Responsibilities:
- Move cursor
- Smooth cursor movement
- Coordinate mapping
- Left click
- Right click
- Double click
- Drag and drop
- Scroll
- Safe mouse release

This class does NOT detect gestures.
GestureDetector/GestureManager decide what should happen.
"""

from __future__ import annotations

import math
import time
from typing import Optional, Tuple

import pyautogui
from pynput.mouse import Button, Controller


class MouseController:
    """
    Controls the operating-system mouse using pynput.

    PyAutoGUI is used only for screen information/utilities.
    Actual mouse events are handled by pynput.
    """

    def __init__(
        self,
        smoothing: float = 0.35,
        sensitivity: float = 1.0,
        click_cooldown: float = 0.30,
        margin: int = 80,
    ):

        # ------------------------------------------------------
        # pynput mouse controller
        # ------------------------------------------------------

        self.mouse = Controller()

        # ------------------------------------------------------
        # Configuration
        # ------------------------------------------------------

        self.smoothing = max(
            0.01,
            min(1.0, float(smoothing)),
        )

        self.sensitivity = max(
            0.1,
            float(sensitivity),
        )

        self.click_cooldown = max(
            0.0,
            float(click_cooldown),
        )

        self.margin = max(
            0,
            int(margin),
        )

        # ------------------------------------------------------
        # Screen dimensions
        # ------------------------------------------------------

        self.screen_width, self.screen_height = (
            pyautogui.size()
        )

        # ------------------------------------------------------
        # Cursor state
        # ------------------------------------------------------

        current_x, current_y = self.mouse.position

        self.current_x = float(current_x)
        self.current_y = float(current_y)

        self.target_x = self.current_x
        self.target_y = self.current_y

        # ------------------------------------------------------
        # Click state
        # ------------------------------------------------------

        self.last_click_time = 0.0

        # ------------------------------------------------------
        # Drag state
        # ------------------------------------------------------

        self.dragging = False

    # ==========================================================
    # SCREEN INFORMATION
    # ==========================================================

    def refresh_screen_size(self) -> Tuple[int, int]:
        """
        Refresh screen dimensions.

        Useful if display resolution changes while application
        is running.
        """

        self.screen_width, self.screen_height = (
            pyautogui.size()
        )

        return (
            self.screen_width,
            self.screen_height,
        )

    def get_screen_size(self) -> Tuple[int, int]:
        """Return current screen dimensions."""

        return (
            self.screen_width,
            self.screen_height,
        )

    # ==========================================================
    # COORDINATE MAPPING
    # ==========================================================

    def map_to_screen(
        self,
        x: float,
        y: float,
        frame_width: int,
        frame_height: int,
    ) -> Tuple[int, int]:
        """
        Convert camera coordinates into screen coordinates.

        A small edge margin is used to prevent the cursor from
        constantly sticking to the very edge of the display.
        """

        if frame_width <= 0 or frame_height <= 0:
            return (
                int(self.current_x),
                int(self.current_y),
            )

        # ------------------------------------------------------
        # Clamp camera coordinates
        # ------------------------------------------------------

        x = max(
            0.0,
            min(float(frame_width - 1), float(x)),
        )

        y = max(
            0.0,
            min(float(frame_height - 1), float(y)),
        )

        # ------------------------------------------------------
        # Effective screen area
        # ------------------------------------------------------

        left = self.margin
        right = max(
            left + 1,
            self.screen_width - self.margin,
        )

        top = self.margin
        bottom = max(
            top + 1,
            self.screen_height - self.margin,
        )

        # ------------------------------------------------------
        # Normalize
        # ------------------------------------------------------

        normalized_x = x / float(frame_width)
        normalized_y = y / float(frame_height)

        # ------------------------------------------------------
        # Apply sensitivity around center
        # ------------------------------------------------------

        center_x = 0.5
        center_y = 0.5

        normalized_x = (
            center_x
            + (normalized_x - center_x)
            * self.sensitivity
        )

        normalized_y = (
            center_y
            + (normalized_y - center_y)
            * self.sensitivity
        )

        normalized_x = max(
            0.0,
            min(1.0, normalized_x),
        )

        normalized_y = max(
            0.0,
            min(1.0, normalized_y),
        )

        screen_x = left + normalized_x * (
            right - left
        )

        screen_y = top + normalized_y * (
            bottom - top
        )

        return (
            int(screen_x),
            int(screen_y),
        )

    # ==========================================================
    # CURSOR MOVEMENT
    # ==========================================================

    def move(
        self,
        x: float,
        y: float,
        frame_width: int,
        frame_height: int,
    ) -> Tuple[int, int]:
        """
        Move cursor using camera coordinates.

        The movement is smoothed using interpolation.
        """

        target_x, target_y = self.map_to_screen(
            x,
            y,
            frame_width,
            frame_height,
        )

        self.target_x = float(target_x)
        self.target_y = float(target_y)

        # ------------------------------------------------------
        # Smooth interpolation
        # ------------------------------------------------------

        self.current_x += (
            self.target_x - self.current_x
        ) * self.smoothing

        self.current_y += (
            self.target_y - self.current_y
        ) * self.smoothing

        final_x = int(
            round(self.current_x)
        )

        final_y = int(
            round(self.current_y)
        )

        # ------------------------------------------------------
        # Send to operating system
        # ------------------------------------------------------

        self.mouse.position = (
            final_x,
            final_y,
        )

        return (
            final_x,
            final_y,
        )

    def move_absolute(
        self,
        x: int,
        y: int,
    ):
        """
        Move cursor directly to absolute screen coordinates.
        """

        x = max(
            0,
            min(self.screen_width - 1, int(x)),
        )

        y = max(
            0,
            min(self.screen_height - 1, int(y)),
        )

        self.current_x = float(x)
        self.current_y = float(y)

        self.target_x = float(x)
        self.target_y = float(y)

        self.mouse.position = (
            x,
            y,
        )

    # ==========================================================
    # LEFT CLICK
    # ==========================================================

    def left_click(self) -> bool:
        """
        Perform a left click.

        Returns:
            True if click occurred.
            False if blocked by cooldown.
        """

        if not self._click_allowed():
            return False

        self.mouse.click(
            Button.left,
            1,
        )

        self.last_click_time = time.monotonic()

        return True

    # ==========================================================
    # RIGHT CLICK
    # ==========================================================

    def right_click(self) -> bool:
        """
        Perform a right click.
        """

        if not self._click_allowed():
            return False

        self.mouse.click(
            Button.right,
            1,
        )

        self.last_click_time = time.monotonic()

        return True

    # ==========================================================
    # DOUBLE CLICK
    # ==========================================================

    def double_click(self) -> bool:
        """
        Perform a double left click.
        """

        if not self._click_allowed():
            return False

        self.mouse.click(
            Button.left,
            2,
        )

        self.last_click_time = time.monotonic()

        return True

    # ==========================================================
    # CLICK HELPERS
    # ==========================================================

    def press_left(self):
        """
        Press and hold the left mouse button.
        """

        if not self.dragging:

            self.mouse.press(
                Button.left
            )

            self.dragging = True

    def release_left(self):
        """
        Release the left mouse button.
        """

        if self.dragging:

            self.mouse.release(
                Button.left
            )

            self.dragging = False

    # ==========================================================
    # DRAG
    # ==========================================================

    def start_drag(self):
        """
        Begin drag operation.
        """

        self.press_left()

    def end_drag(self):
        """
        End drag operation.
        """

        self.release_left()

    def is_dragging(self) -> bool:
        """Return current drag state."""

        return self.dragging

    # ==========================================================
    # SCROLL
    # ==========================================================

    def scroll(
        self,
        amount: int,
    ):
        """
        Scroll vertically.

        Positive values scroll up.
        Negative values scroll down.
        """

        amount = int(amount)

        if amount == 0:
            return

        self.mouse.scroll(
            0,
            amount,
        )

    def scroll_up(
        self,
        amount: int = 1,
    ):
        """Scroll upward."""

        self.scroll(
            abs(int(amount))
        )

    def scroll_down(
        self,
        amount: int = 1,
    ):
        """Scroll downward."""

        self.scroll(
            -abs(int(amount))
        )

    # ==========================================================
    # COOLDOWN
    # ==========================================================

    def _click_allowed(self) -> bool:

        now = time.monotonic()

        return (
            now - self.last_click_time
            >= self.click_cooldown
        )

    # ==========================================================
    # EMERGENCY RELEASE
    # ==========================================================

    def release_all(self):
        """
        Safely release any held mouse buttons.

        Always call this when:
        - application stops
        - camera disconnects
        - an exception occurs
        """

        try:

            self.mouse.release(
                Button.left
            )

        except Exception:
            pass

        self.dragging = False

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset controller state without moving the cursor.
        """

        self.release_all()

        current_x, current_y = (
            self.mouse.position
        )

        self.current_x = float(current_x)
        self.current_y = float(current_y)

        self.target_x = self.current_x
        self.target_y = self.current_y

        self.last_click_time = 0.0

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Safely shut down the mouse controller.
        """

        self.release_all()

