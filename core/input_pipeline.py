"""
input_pipeline.py
-----------------
End-to-end processing pipeline.

Camera frame
    ↓
HandTracker
    ↓
GestureDetector
    ↓
GestureManager
    ↓
MouseController / MediaController /
PresentationController / ScreenshotController
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector
from core.gesture_manager import GestureManager
from controllers.mouse_controller import MouseController
from controllers.media_controller import MediaController
from controllers.presentation_controller import PresentationController
from controllers.screenshot_controller import ScreenshotController


class InputPipeline:

    # ==========================================================
    # ROUTED EVENTS
    # ==========================================================

    MEDIA_EVENTS = (
        "VOLUME_UP",
        "VOLUME_DOWN",
        "MUTE",
        "PLAY_PAUSE",
        "NEXT_TRACK",
        "PREV_TRACK",
    )

    SLIDE_EVENTS = (
        "NEXT_SLIDE",
        "PREV_SLIDE",
        "START_PRESENTATION",
        "END_PRESENTATION",
        "BLANK_SCREEN",
    )

    def __init__(
        self,
        hand_tracker: Optional[HandTracker] = None,
        gesture_detector: Optional[GestureDetector] = None,
        gesture_manager: Optional[GestureManager] = None,
        mouse_controller: Optional[MouseController] = None,
        media_controller: Optional[MediaController] = None,
        presentation_controller: Optional[PresentationController] = None,
        screenshot_controller: Optional[ScreenshotController] = None,
    ):

        self.hand_tracker = (
            hand_tracker
            if hand_tracker is not None
            else HandTracker(
                max_hands=2,
                detection_confidence=0.7,
                tracking_confidence=0.7,
            )
        )

        self.gesture_detector = (
            gesture_detector
            if gesture_detector is not None
            else GestureDetector()
        )

        self.gesture_manager = (
            gesture_manager
            if gesture_manager is not None
            else GestureManager()
        )

        self.mouse_controller = (
            mouse_controller
            if mouse_controller is not None
            else MouseController()
        )

        self.media_controller = (
            media_controller
            if media_controller is not None
            else MediaController()
        )

        self.presentation_controller = (
            presentation_controller
            if presentation_controller is not None
            else PresentationController()
        )

        self.screenshot_controller = (
            screenshot_controller
            if screenshot_controller is not None
            else ScreenshotController()
        )

        self.enabled = True

        self.last_result = self._empty_result()

    # ==========================================================
    # PROCESS
    # ==========================================================

    def process(self, frame) -> Dict[str, Any]:

        if frame is None:

            return self._empty_result()

        if not self.enabled:

            return self._empty_result()

        try:

            # --------------------------------------------------
            # 1. Hand tracking
            # --------------------------------------------------

            hand_data = self.hand_tracker.detect(frame)

            if hand_data is None:

                hand_data = {}

            # --------------------------------------------------
            # 2. Draw landmarks
            # --------------------------------------------------

            processed_frame = frame

            results = hand_data.get(
                "results"
            )

            if results is not None:

                processed_frame = (
                    self.hand_tracker.draw_landmarks(
                        frame,
                        results,
                    )
                )

            # --------------------------------------------------
            # 3. Gesture detection
            # --------------------------------------------------

            detection = (
                self.gesture_detector.detect(
                    hand_data
                )
            )

            if detection is None:

                detection = {
                    "gesture": "NONE",
                    "hand_detected": False,
                    "confidence": 0.0,
                }

            # --------------------------------------------------
            # 4. Gesture manager
            # --------------------------------------------------

            managed = (
                self.gesture_manager.update(
                    detection
                )
            )

            # --------------------------------------------------
            # 5. Execute action
            # --------------------------------------------------

            action_result = self._execute(
                managed,
                frame,
            )

            result = {

                "frame": processed_frame,

                "gesture": managed.get(
                    "gesture",
                    "NONE",
                ),

                "stable": managed.get(
                    "stable",
                    False,
                ),

                "event": managed.get(
                    "event"
                ),

                "action": action_result.get(
                    "action"
                ),

                "hand_detected": managed.get(
                    "hand_detected",
                    detection.get(
                        "hand_detected",
                        False,
                    ),
                ),

                "confidence": managed.get(
                    "confidence",
                    detection.get(
                        "confidence",
                        0.0,
                    ),
                ),

                "handedness": detection.get(
                    "handedness",
                    "Unknown",
                ),

                "landmarks": detection.get(
                    "landmarks",
                    [],
                ),

                "fingers": detection.get(
                    "fingers",
                    {},
                ),

                "pinch": detection.get(
                    "pinch",
                    {},
                ),

                "position": detection.get(
                    "position"
                ),

                "motion": detection.get(
                    "motion",
                    {},
                ),

                "cursor": action_result.get(
                    "cursor"
                ),
            }

            self.last_result = result

            return result

        except Exception as e:

            print(
                f"[InputPipeline] Error: {e}"
            )

            return {
                "frame": frame,
                "gesture": "ERROR",
                "stable": False,
                "event": None,
                "action": None,
                "hand_detected": False,
                "confidence": 0.0,
                "handedness": "Unknown",
                "landmarks": [],
                "fingers": {},
                "pinch": {},
                "position": None,
                "cursor": None,
            }

    # ==========================================================
    # ACTION EXECUTION
    # ==========================================================

    def _execute(
        self,
        managed: Dict[str, Any],
        frame,
    ) -> Dict[str, Any]:

        gesture = managed.get(
            "gesture",
            "NONE",
        )

        event = managed.get(
            "event"
        )

        detection = (
            managed.get("data")
            or {}
        )

        # ------------------------------------------------------
        # MEDIA
        # ------------------------------------------------------

        if event in self.MEDIA_EVENTS:

            if self.media_controller.handle_event(event):

                return {
                    "action": event,
                    "cursor": self._cursor_position(),
                }

            return {
                "action": None,
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # SLIDES
        # ------------------------------------------------------

        if event in self.SLIDE_EVENTS:

            if self.presentation_controller.handle_event(event):

                return {
                    "action": event,
                    "cursor": self._cursor_position(),
                }

            return {
                "action": None,
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # SCREENSHOT
        # ------------------------------------------------------

        if event == "SCREENSHOT":

            if self.screenshot_controller.handle_event(event):

                return {
                    "action": "SCREENSHOT",
                    "cursor": self._cursor_position(),
                }

            return {
                "action": None,
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # MOVE
        # ------------------------------------------------------

        position = detection.get(
            "position"
        )

        if (
            event == "MOVE"
            and position is not None
        ):

            cursor = self._move_cursor(
                position,
                frame,
            )

            return {
                "action": "MOVE",
                "cursor": cursor,
            }

        # ------------------------------------------------------
        # LEFT CLICK
        # ------------------------------------------------------

        if event == "LEFT_CLICK":

            if self.mouse_controller.left_click():

                return {
                    "action": "LEFT_CLICK",
                    "cursor": self._cursor_position(),
                }

        # ------------------------------------------------------
        # RIGHT CLICK
        # ------------------------------------------------------

        if event == "RIGHT_CLICK":

            if self.mouse_controller.right_click():

                return {
                    "action": "RIGHT_CLICK",
                    "cursor": self._cursor_position(),
                }

        # ------------------------------------------------------
        # DOUBLE CLICK
        # ------------------------------------------------------

        if event == "DOUBLE_CLICK":

            if self.mouse_controller.double_click():

                return {
                    "action": "DOUBLE_CLICK",
                    "cursor": self._cursor_position(),
                }

        # ------------------------------------------------------
        # DRAG START
        # ------------------------------------------------------

        if event == "DRAG_START":

            self.mouse_controller.start_drag()

            return {
                "action": "DRAG_START",
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # DRAG HOLD
        # ------------------------------------------------------

        if event == "DRAG_HOLD":

            if position is not None:

                cursor = self._move_cursor(
                    position,
                    frame,
                )

                return {
                    "action": "DRAG_HOLD",
                    "cursor": cursor,
                }

            return {
                "action": "DRAG_HOLD",
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # DRAG END
        # ------------------------------------------------------

        if event == "DRAG_END":

            self.mouse_controller.end_drag()

            return {
                "action": "DRAG_END",
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # SCROLL
        # ------------------------------------------------------

        if event == "SCROLL_UP":

            self.mouse_controller.scroll_up()

            return {
                "action": "SCROLL_UP",
                "cursor": self._cursor_position(),
            }

        if event == "SCROLL_DOWN":

            self.mouse_controller.scroll_down()

            return {
                "action": "SCROLL_DOWN",
                "cursor": self._cursor_position(),
            }

        if event == "SCROLL":

            self.mouse_controller.scroll(1)

            return {
                "action": "SCROLL",
                "cursor": self._cursor_position(),
            }

        # ------------------------------------------------------
        # Other events
        # ------------------------------------------------------

        if event in (
            "SWIPE_LEFT",
            "SWIPE_RIGHT",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "OPEN_PALM",
        ):

            return {
                "action": event,
                "cursor": self._cursor_position(),
            }

        return {
            "action": None,
            "cursor": self._cursor_position(),
        }

    # ==========================================================
    # CURSOR
    # ==========================================================

    def _move_cursor(
        self,
        position,
        frame,
    ):
        """
        Drive the cursor from a landmark position.

        GestureDetector reports MediaPipe normalized coordinates
        (0.0 - 1.0), while MouseController.map_to_screen expects
        camera pixels, so the conversion happens here.
        """

        try:

            frame_height, frame_width = (
                frame.shape[:2]
            )

        except Exception:

            return self._cursor_position()

        x, y = position

        return self.mouse_controller.move(
            float(x) * frame_width,
            float(y) * frame_height,
            frame_width,
            frame_height,
        )

    def _cursor_position(self):

        try:

            return tuple(
                self.mouse_controller.mouse.position
            )

        except Exception:

            return None

    # ==========================================================
    # ENABLE
    # ==========================================================

    def enable(self):

        self.enabled = True

        self.gesture_manager.enable()

    # ==========================================================
    # DISABLE
    # ==========================================================

    def disable(self):

        self.enabled = False

        try:

            self.gesture_manager.force_end_drag()

        except Exception:

            pass

        self.mouse_controller.release_all()

        self.media_controller.release_all()

        self.presentation_controller.release_all()

        self.gesture_manager.disable()

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.gesture_manager.reset()

        self.mouse_controller.reset()

        self.media_controller.reset()

        self.presentation_controller.reset()

        self.screenshot_controller.reset()

        self.last_result = (
            self._empty_result()
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):

        self.disable()

        try:

            self.hand_tracker.close()

        except Exception:

            pass

        try:

            self.mouse_controller.close()

        except Exception:

            pass

        try:

            self.media_controller.close()

        except Exception:

            pass

        try:

            self.presentation_controller.close()

        except Exception:

            pass

        try:

            self.screenshot_controller.close()

        except Exception:

            pass

    # ==========================================================
    # LAST RESULT
    # ==========================================================

    def get_last_result(self):

        return self.last_result

    # ==========================================================
    # EMPTY RESULT
    # ==========================================================

    @staticmethod
    def _empty_result():

        return {
            "frame": None,
            "gesture": "NONE",
            "stable": False,
            "event": None,
            "action": None,
            "hand_detected": False,
            "confidence": 0.0,
            "handedness": "Unknown",
            "landmarks": [],
            "fingers": {},
            "pinch": {},
            "position": None,
            "motion": {},
            "cursor": None,
        }