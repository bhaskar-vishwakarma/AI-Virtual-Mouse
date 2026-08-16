"""
frame_processor.py
------------------
Coordinates the complete processing pipeline.

Pipeline:
Camera
    ↓
HandTracker
    ↓
GestureDetector
    ↓
GestureManager
    ↓
Processed Output
"""

from __future__ import annotations

from typing import Dict, Any


class FrameProcessor:
    """
    Central processing pipeline.
    """

    def __init__(
        self,
        hand_tracker,
        gesture_detector,
        gesture_manager,
        mode_manager,
    ):
        self.hand_tracker = hand_tracker
        self.gesture_detector = gesture_detector
        self.gesture_manager = gesture_manager
        self.mode_manager = mode_manager

    # ==========================================================
    # Process Frame
    # ==========================================================

    def process(self, frame) -> Dict[str, Any]:

        try:

            # ---------------------------------------------
            # Hand Detection
            # ---------------------------------------------

            hand_data = self.hand_tracker.detect(frame)

            frame = hand_data["frame"]
            hands = hand_data["hands"]

            mode = self.mode_manager.current_mode

            # ---------------------------------------------
            # No Hand
            # ---------------------------------------------

            if not hands:

                return {
                    "frame": frame,
                    "gesture": "NONE",
                    "hand_detected": False,
                    "hands": [],
                    "mode": mode,
                }

            # ---------------------------------------------
            # Detect Gesture
            # ---------------------------------------------

            gesture_data = self.gesture_detector.detect(
                hands,
                mode,
            )

            # ---------------------------------------------
            # Execute Gesture
            # ---------------------------------------------

            self.gesture_manager.execute(
                gesture_data
            )

            return {
                "frame": frame,
                "gesture": gesture_data["gesture"],
                "hand_detected": True,
                "hands": hands,
                "mode": mode,
            }

        except Exception as e:

            print(f"[FrameProcessor] {e}")

            return {
                "frame": frame,
                "gesture": "ERROR",
                "hand_detected": False,
                "hands": [],
                "mode": "UNKNOWN",
            }