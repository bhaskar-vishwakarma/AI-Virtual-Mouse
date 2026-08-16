"""
gesture_manager.py
------------------
Gesture stability, cooldown, and action-event management.

Responsibilities:
- Stabilize noisy gesture detection
- Prevent repeated accidental actions
- Handle gesture cooldowns
- Track gesture state
- Convert detected gestures into one-shot events

This class does NOT directly control the mouse, keyboard,
volume, brightness, etc.

Controllers are responsible for performing actions.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Dict, Optional


class GestureManager:
    """
    Manages gesture state and prevents accidental repeated actions.

    Example:

        Detector:
            LEFT_CLICK
            LEFT_CLICK
            LEFT_CLICK
            LEFT_CLICK

        Manager:
            LEFT_CLICK_EVENT
            NONE
            NONE
            NONE

    This allows a held gesture to trigger only once.
    """

    # ==========================================================
    # MEDIA GESTURE MAP
    # ==========================================================

    MEDIA_EVENTS = {
        "FOUR_FINGER": "VOLUME_UP",
        "PINKY": "VOLUME_DOWN",
        "THREE_FINGER": "PLAY_PAUSE",
        "THUMB_DOWN": "MUTE",
        "ROCK": "NEXT_TRACK",
        "CALL": "PREV_TRACK",
    }

    # Media events that repeat while the gesture is held.
    REPEATING_MEDIA_EVENTS = (
        "VOLUME_UP",
        "VOLUME_DOWN",
    )

    def __init__(
        self,
        stability_frames: int = 3,
        click_cooldown: float = 0.25,
        double_click_window: float = 0.45,
        action_cooldown: float = 0.30,
        media_cooldown: float = 0.45,
        volume_repeat: float = 0.12,
        scroll_repeat: float = 0.10,
        scroll_threshold: float = 0.020,
        swipe_threshold: float = 0.150,
        slide_cooldown: float = 0.70,
        screenshot_cooldown: float = 1.50,
    ):

        self.stability_frames = max(
            1,
            int(stability_frames),
        )

        self.click_cooldown = max(
            0.0,
            float(click_cooldown),
        )

        self.double_click_window = max(
            0.0,
            float(double_click_window),
        )

        self.action_cooldown = max(
            0.0,
            float(action_cooldown),
        )

        self.media_cooldown = max(
            0.0,
            float(media_cooldown),
        )

        self.volume_repeat = max(
            0.0,
            float(volume_repeat),
        )

        self.scroll_repeat = max(
            0.0,
            float(scroll_repeat),
        )

        # Minimum normalized vertical travel before a held
        # TWO_FINGER pose counts as a scroll.
        self.scroll_threshold = max(
            0.001,
            float(scroll_threshold),
        )

        # Minimum normalized horizontal travel before a moving
        # INDEX pose counts as a slide swipe.
        self.swipe_threshold = max(
            0.010,
            float(swipe_threshold),
        )

        self.slide_cooldown = max(
            0.0,
            float(slide_cooldown),
        )

        # How long the cursor stays parked after a slide swipe, so
        # finishing the sweep does not fling the pointer.
        self.swipe_settle = max(
            0.0,
            float(slide_cooldown) * 0.5,
        )

        self.screenshot_cooldown = max(
            0.0,
            float(screenshot_cooldown),
        )

        # ------------------------------------------------------
        # Gesture history
        # ------------------------------------------------------

        self.gesture_history = deque(
            maxlen=self.stability_frames
        )

        self.current_gesture = "NONE"
        self.previous_gesture = "NONE"

        self.stable_gesture = "NONE"

        # ------------------------------------------------------
        # Timing
        # ------------------------------------------------------

        self.last_action_time = 0.0
        self.last_click_time = 0.0
        self.last_media_time = 0.0
        self.last_volume_time = 0.0
        self.last_scroll_time = 0.0
        self.last_slide_time = 0.0
        self.last_shot_time = 0.0

        # ------------------------------------------------------
        # State
        # ------------------------------------------------------

        self.is_dragging = False
        self.is_active = True

        # Last media gesture that actually fired. Used for edge
        # triggering, since previous_gesture is already equal to
        # the current gesture by the time it becomes stable.
        self.last_media_gesture: Optional[str] = None

        # Same edge-trigger guard for the screenshot pose.
        self.last_shot_gesture: Optional[str] = None

        # Same edge-trigger guard for the click poses, so a held
        # pinch clicks once instead of repeating.
        self.last_click_gesture: Optional[str] = None

        # Used for detecting two consecutive clicks.
        self.click_count = 0

    # ==========================================================
    # MAIN UPDATE
    # ==========================================================

    def update(
        self,
        detection: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update gesture state from GestureDetector output.

        Returns:

        {
            "gesture": str,
            "stable": bool,
            "event": Optional[str],
            "hand_detected": bool,
            "confidence": float,
            "data": original detection
        }
        """

        if not self.is_active:

            return self._empty_state(
                detection
            )

        if not detection:

            self._reset_gesture_state()

            return self._empty_state(
                detection
            )

        gesture = detection.get(
            "gesture",
            "NONE",
        )

        hand_detected = bool(
            detection.get(
                "hand_detected",
                False,
            )
        )

        confidence = float(
            detection.get(
                "confidence",
                0.0,
            )
        )

        if not hand_detected:

            self._reset_gesture_state()

            return {
                "gesture": "NONE",
                "stable": False,
                "event": None,
                "hand_detected": False,
                "confidence": confidence,
                "data": detection,
            }

        self.previous_gesture = (
            self.current_gesture
        )

        self.current_gesture = gesture

        # ------------------------------------------------------
        # Add gesture to stability history
        # ------------------------------------------------------

        self.gesture_history.append(
            gesture
        )

        stable = self._is_stable()

        if stable:

            self.stable_gesture = gesture

        # ------------------------------------------------------
        # Determine one-shot event
        # ------------------------------------------------------

        event = None

        if stable:

            event = self._generate_event(
                gesture,
                detection,
            )

        return {
            "gesture": gesture,
            "stable": stable,
            "event": event,
            "hand_detected": True,
            "confidence": confidence,
            "data": detection,
        }

    # ==========================================================
    # STABILITY
    # ==========================================================

    def _is_stable(self) -> bool:
        """
        Returns True when the same gesture has been detected
        for the configured number of consecutive frames.
        """

        if (
            len(self.gesture_history)
            < self.stability_frames
        ):
            return False

        return all(
            gesture == self.gesture_history[0]
            for gesture in self.gesture_history
        )

    # ==========================================================
    # EVENT GENERATION
    # ==========================================================

    def _generate_event(
        self,
        gesture: str,
        detection: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Convert stable gestures into one-shot events.

        Continuous gestures such as MOVE and SCROLL are returned
        as events differently from one-shot gestures such as
        LEFT_CLICK.

        Motion-qualified gestures (scroll, slide swipe) read the
        motion vector supplied by GestureDetector.
        """

        now = time.monotonic()

        motion = (
            (detection or {}).get("motion")
            or {}
        )

        # ------------------------------------------------------
        # Screenshot
        # ------------------------------------------------------

        if gesture != "THUMB_UP":

            self.last_shot_gesture = None

        else:

            if self.last_shot_gesture == gesture:
                return None

            if (
                now - self.last_shot_time
                < self.screenshot_cooldown
            ):
                return None

            self.last_shot_time = now

            self.last_shot_gesture = gesture

            return "SCREENSHOT"

        # ------------------------------------------------------
        # Scroll  (TWO_FINGER moved vertically)
        # ------------------------------------------------------

        if gesture == "TWO_FINGER":

            return self._generate_scroll_event(
                motion,
                now,
            )

        # ------------------------------------------------------
        # Cursor move / slide swipe  (INDEX)
        # ------------------------------------------------------

        if gesture != "PINCH" and gesture != "OK":

            self.last_click_gesture = None

        if gesture == "INDEX":

            slide = self._generate_slide_event(
                motion,
                now,
            )

            if slide is not None:

                return slide

            # A deliberate sweep should change the slide without
            # also hurling the cursor across the screen.

            if self._is_swiping(motion, now):

                return None

            return "MOVE"

        # ------------------------------------------------------
        # Left click  (PINCH)
        # ------------------------------------------------------

        if gesture == "PINCH":

            return self._generate_click_event(
                "LEFT_CLICK",
                now,
            )

        # ------------------------------------------------------
        # Right click  (OK)
        # ------------------------------------------------------

        if gesture == "OK":

            return self._generate_click_event(
                "RIGHT_CLICK",
                now,
            )

        # ------------------------------------------------------
        # Media gestures
        # ------------------------------------------------------

        media_event = self.MEDIA_EVENTS.get(
            gesture
        )

        if media_event is None:

            # Leaving the media gesture re-arms edge triggering.
            self.last_media_gesture = None

        else:

            return self._generate_media_event(
                gesture,
                media_event,
                now,
            )

        # ------------------------------------------------------
        # Cursor movement
        # ------------------------------------------------------

        if gesture == "MOVE":

            return "MOVE"

        # ------------------------------------------------------
        # Scroll
        # ------------------------------------------------------

        if gesture == "SCROLL":

            if (
                now - self.last_action_time
                >= self.action_cooldown
            ):

                self.last_action_time = now

                return "SCROLL"

            return None

        # ------------------------------------------------------
        # Left click
        # ------------------------------------------------------

        if gesture == "LEFT_CLICK":

            if (
                now - self.last_click_time
                < self.click_cooldown
            ):
                return None

            self.last_click_time = now
            self.last_action_time = now

            return "LEFT_CLICK"

        # ------------------------------------------------------
        # Right click
        # ------------------------------------------------------

        if gesture == "RIGHT_CLICK":

            if (
                now - self.last_action_time
                < self.click_cooldown
            ):
                return None

            self.last_action_time = now

            return "RIGHT_CLICK"

        # ------------------------------------------------------
        # Fist
        # ------------------------------------------------------

        if gesture == "FIST":

            # Fist is used as a state rather than a repeated
            # action. The controller can use this for drag.

            if not self.is_dragging:

                self.is_dragging = True

                return "DRAG_START"

            return "DRAG_HOLD"

        # ------------------------------------------------------
        # Open palm
        # ------------------------------------------------------

        if gesture == "OPEN_PALM":

            if self.is_dragging:

                self.is_dragging = False

                return "DRAG_END"

            return "OPEN_PALM"

        # ------------------------------------------------------
        # Swipe left
        # ------------------------------------------------------

        if gesture == "SWIPE_LEFT":

            if (
                now - self.last_action_time
                >= self.action_cooldown
            ):

                self.last_action_time = now

                return "SWIPE_LEFT"

            return None

        # ------------------------------------------------------
        # Swipe right
        # ------------------------------------------------------

        if gesture == "SWIPE_RIGHT":

            if (
                now - self.last_action_time
                >= self.action_cooldown
            ):

                self.last_action_time = now

                return "SWIPE_RIGHT"

            return None

        # ------------------------------------------------------
        # Thumbs up
        # ------------------------------------------------------

        if gesture == "THUMBS_UP":

            if (
                self.previous_gesture
                != "THUMBS_UP"
                and now - self.last_action_time
                >= self.action_cooldown
            ):

                self.last_action_time = now

                return "THUMBS_UP"

            return None

        # ------------------------------------------------------
        # Thumbs down
        # ------------------------------------------------------

        if gesture == "THUMBS_DOWN":

            if (
                self.previous_gesture
                != "THUMBS_DOWN"
                and now - self.last_action_time
                >= self.action_cooldown
            ):

                self.last_action_time = now

                return "THUMBS_DOWN"

            return None

        return None

    # ==========================================================
    # SCROLL EVENTS
    # ==========================================================

    def _generate_scroll_event(
        self,
        motion: Dict[str, Any],
        now: float,
    ) -> Optional[str]:
        """
        Convert a held TWO_FINGER pose plus vertical hand travel
        into a repeating scroll event.

        A stationary TWO_FINGER pose produces nothing, so resting
        the hand in that shape does not scroll the page.
        """

        if motion.get("axis") != "VERTICAL":
            return None

        dy = float(
            motion.get(
                "dy",
                0.0,
            )
        )

        if abs(dy) < self.scroll_threshold:
            return None

        if (
            now - self.last_scroll_time
            < self.scroll_repeat
        ):
            return None

        self.last_scroll_time = now

        # MediaPipe y grows downward, so a hand moving down
        # scrolls the page down.

        if dy > 0:
            return "SCROLL_DOWN"

        return "SCROLL_UP"

    # ==========================================================
    # SLIDE EVENTS
    # ==========================================================

    def _generate_slide_event(
        self,
        motion: Dict[str, Any],
        now: float,
    ) -> Optional[str]:
        """
        Convert a pointing INDEX pose swept horizontally into a
        one-shot slide event.

        The swipe threshold is deliberately large so that simply
        holding a pointing finger still does nothing.
        """

        if motion.get("axis") != "HORIZONTAL":
            return None

        dx = float(
            motion.get(
                "dx",
                0.0,
            )
        )

        if abs(dx) < self.swipe_threshold:
            return None

        if (
            now - self.last_slide_time
            < self.slide_cooldown
        ):
            return None

        self.last_slide_time = now

        # The camera frame is mirrored, so a rightward sweep on
        # screen matches the user's own rightward sweep.

        if dx > 0:
            return "NEXT_SLIDE"

        return "PREV_SLIDE"

    # ==========================================================
    # SWIPE STATE
    # ==========================================================

    def _is_swiping(
        self,
        motion: Dict[str, Any],
        now: float,
    ) -> bool:
        """
        Return True while a slide sweep is in progress, including a
        short settle window after one fires.
        """

        if (
            now - self.last_slide_time
            < self.swipe_settle
        ):
            return True

        if motion.get("axis") != "HORIZONTAL":
            return False

        dx = float(
            motion.get(
                "dx",
                0.0,
            )
        )

        return abs(dx) >= self.swipe_threshold

    # ==========================================================
    # CLICK EVENTS
    # ==========================================================

    def _generate_click_event(
        self,
        event: str,
        now: float,
    ) -> Optional[str]:
        """
        Convert a held click pose into a single click.

        The pose must be released and re-formed to click again, so
        resting in a pinch does not autofire. Two quick pinches sit
        inside the operating system's own double-click window and
        are handled as a double click by the OS.
        """

        if self.last_click_gesture == event:
            return None

        if (
            now - self.last_click_time
            < self.click_cooldown
        ):
            return None

        self.last_click_time = now
        self.last_action_time = now

        self.last_click_gesture = event

        return event

    # ==========================================================
    # MEDIA EVENTS
    # ==========================================================

    def _generate_media_event(
        self,
        gesture: str,
        media_event: str,
        now: float,
    ) -> Optional[str]:
        """
        Convert a stable media gesture into an event.

        Volume gestures repeat while held so the level ramps.
        Transport gestures (play/pause, mute, next, previous)
        fire once per gesture entry.
        """

        # ------------------------------------------------------
        # Switching between two media gestures re-arms the
        # one-shot edge trigger.
        # ------------------------------------------------------

        if (
            self.last_media_gesture is not None
            and self.last_media_gesture != gesture
        ):

            self.last_media_gesture = None

        # ------------------------------------------------------
        # Repeating: volume up / down
        # ------------------------------------------------------

        if media_event in self.REPEATING_MEDIA_EVENTS:

            if (
                now - self.last_volume_time
                < self.volume_repeat
            ):
                return None

            self.last_volume_time = now

            return media_event

        # ------------------------------------------------------
        # One-shot: play/pause, mute, next, previous
        # ------------------------------------------------------

        if self.last_media_gesture == gesture:
            return None

        if (
            now - self.last_media_time
            < self.media_cooldown
        ):
            return None

        self.last_media_time = now

        self.last_media_gesture = gesture

        return media_event

    # ==========================================================
    # DOUBLE CLICK
    # ==========================================================

    def register_click(self) -> Optional[str]:
        """
        Optional helper for double-click detection.

        Call this whenever a LEFT_CLICK event is generated.

        Returns:
            "DOUBLE_CLICK" when two clicks occur within the
            configured time window.
            Otherwise None.
        """

        now = time.monotonic()

        if (
            now - self.last_click_time
            <= self.double_click_window
        ):

            self.click_count += 1

        else:

            self.click_count = 1

        self.last_click_time = now

        if self.click_count >= 2:

            self.click_count = 0

            return "DOUBLE_CLICK"

        return None

    # ==========================================================
    # DRAG
    # ==========================================================

    def force_end_drag(self) -> Optional[str]:
        """
        Forcefully end drag state.

        Useful when:
        - Camera is disconnected
        - Hand disappears
        - Application is stopped
        """

        if self.is_dragging:

            self.is_dragging = False

            return "DRAG_END"

        return None

    # ==========================================================
    # RESET
    # ==========================================================

    def _reset_gesture_state(self):

        self.gesture_history.clear()

        self.previous_gesture = (
            self.current_gesture
        )

        self.current_gesture = "NONE"
        self.stable_gesture = "NONE"

        self.last_media_gesture = None
        self.last_shot_gesture = None
        self.last_click_gesture = None

    def reset(self):

        self._reset_gesture_state()

        self.last_action_time = 0.0
        self.last_click_time = 0.0
        self.last_media_time = 0.0
        self.last_volume_time = 0.0
        self.last_scroll_time = 0.0
        self.last_slide_time = 0.0
        self.last_shot_time = 0.0

        self.is_dragging = False
        self.click_count = 0

    # ==========================================================
    # ENABLE / DISABLE
    # ==========================================================

    def enable(self):

        self.is_active = True

    def disable(self):

        self.is_active = False

        self.reset()

    # ==========================================================
    # STATUS
    # ==========================================================

    def get_current_gesture(self) -> str:

        return self.current_gesture

    def get_stable_gesture(self) -> str:

        return self.stable_gesture

    def get_drag_state(self) -> bool:

        return self.is_dragging

    # ==========================================================
    # EMPTY STATE
    # ==========================================================

    @staticmethod
    def _empty_state(
        detection: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        confidence = 0.0

        if detection:

            confidence = float(
                detection.get(
                    "confidence",
                    0.0,
                )
            )

        return {
            "gesture": "NONE",
            "stable": False,
            "event": None,
            "hand_detected": False,
            "confidence": confidence,
            "data": detection,
        }

