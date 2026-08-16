"""
screenshot_controller.py
------------------------
Screen capture controller for AI Virtual Mouse Pro v3.0.

Uses:
    pyautogui -> full screen capture

Responsibilities:
- Capture the full screen
- Write timestamped PNG files
- Enforce a capture cooldown
- Track the most recent capture

Captures are written to data/screenshots relative to the project
root. The directory is created on demand.

This class does NOT detect gestures.
GestureDetector/GestureManager decide what should happen.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import pyautogui


class ScreenshotController:
    """
    Saves full-screen captures to disk.

    A relatively long cooldown is used by default because a single
    intentional gesture can easily stay stable for many frames.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        action_cooldown: float = 1.50,
        filename_prefix: str = "shot",
    ):

        # ------------------------------------------------------
        # Configuration
        # ------------------------------------------------------

        self.action_cooldown = max(
            0.0,
            float(action_cooldown),
        )

        self.filename_prefix = (
            str(filename_prefix).strip()
            or "shot"
        )

        # ------------------------------------------------------
        # Output directory
        # ------------------------------------------------------

        if output_dir is None:

            project_root = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

            output_dir = os.path.join(
                project_root,
                "data",
                "screenshots",
            )

        self.output_dir = str(output_dir)

        self._ensure_output_dir()

        # ------------------------------------------------------
        # Timing state
        # ------------------------------------------------------

        self.last_action_time = 0.0

        # ------------------------------------------------------
        # Capture state
        # ------------------------------------------------------

        self.last_path: Optional[str] = None

        self.capture_count = 0

    # ==========================================================
    # OUTPUT DIRECTORY
    # ==========================================================

    def _ensure_output_dir(self) -> bool:

        # A stray zero-byte file can occupy the target path, which
        # makes makedirs fail with a confusing FileExistsError.
        # Repair it when possible, and fall back to a sibling
        # directory rather than losing the capture.

        if (
            os.path.exists(self.output_dir)
            and not os.path.isdir(self.output_dir)
        ):

            try:

                os.remove(
                    self.output_dir
                )

                print(
                    f"[ScreenshotController] Replaced stray file "
                    f"{self.output_dir} with a directory"
                )

            except Exception:

                fallback = (
                    f"{self.output_dir.rstrip(os.sep)}_out"
                )

                print(
                    f"[ScreenshotController] {self.output_dir} is a "
                    f"file, falling back to {fallback}"
                )

                self.output_dir = fallback

        try:

            os.makedirs(
                self.output_dir,
                exist_ok=True,
            )

            return True

        except Exception as e:

            print(
                f"[ScreenshotController] Cannot create {self.output_dir}: {e}"
            )

            return False

    # ==========================================================
    # FILENAME
    # ==========================================================

    def _build_path(self) -> str:

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )[:-3]

        filename = (
            f"{self.filename_prefix}_{stamp}.png"
        )

        return os.path.join(
            self.output_dir,
            filename,
        )

    # ==========================================================
    # COOLDOWN
    # ==========================================================

    def _action_allowed(self) -> bool:

        now = time.monotonic()

        return (
            now - self.last_action_time
            >= self.action_cooldown
        )

    # ==========================================================
    # CAPTURE
    # ==========================================================

    def capture(self) -> Optional[str]:
        """
        Capture the full screen.

        Returns:
            Absolute path of the saved PNG.
            None if blocked by cooldown or the capture failed.
        """

        if not self._action_allowed():
            return None

        if not self._ensure_output_dir():
            return None

        path = self._build_path()

        try:

            image = pyautogui.screenshot()

            image.save(
                path
            )

        except Exception as e:

            print(
                f"[ScreenshotController] Capture failed: {e}"
            )

            return None

        self.last_action_time = (
            time.monotonic()
        )

        self.last_path = path

        self.capture_count += 1

        print(
            f"[ScreenshotController] Saved {path}"
        )

        return path

    # ==========================================================
    # EVENT DISPATCH
    # ==========================================================

    def handle_event(
        self,
        event: str,
    ) -> bool:
        """
        Execute a capture event name produced by GestureManager.

        Returns True when a capture was written.
        """

        if not event:
            return False

        if event == "SCREENSHOT":

            return (
                self.capture()
                is not None
            )

        return False

    # ==========================================================
    # STATUS
    # ==========================================================

    def get_last_path(self) -> Optional[str]:
        """Return the path of the most recent capture."""

        return self.last_path

    def get_capture_count(self) -> int:
        """Return the number of captures this session."""

        return self.capture_count

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset controller timing state.
        """

        self.last_action_time = 0.0

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Safely shut down the screenshot controller.
        """

        self.last_action_time = 0.0
