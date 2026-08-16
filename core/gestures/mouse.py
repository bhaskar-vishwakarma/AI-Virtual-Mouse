"""
mouse.py
--------
Mouse gesture recognition.

This module classifies hand poses into mouse gestures.
It does NOT perform mouse actions.
"""

from __future__ import annotations

from .finger_state import FingerState
from .pinch import PinchDetector

class MouseGestures:
    """
    Mouse gesture recognizer.
    """

    def __init__(self):
        self.fingers = FingerState()
        self.pinch = PinchDetector()

    # ==========================================================
    # Detect
    # ==========================================================

    def detect(
        self,
        landmarks: list,
        hand_type: str = "Right"
    ) -> str:
        """
        Returns one of:

        MOVE
        LEFT_CLICK
        RIGHT_CLICK
        DRAG
        SCROLL
        IDLE
        """

        states = self.fingers.get_states(
            landmarks,
            hand_type
        )

        # --------------------------------------------------
        # Left Click
        # Thumb + Index Pinch
        # --------------------------------------------------

        if self.pinch.thumb_index(landmarks):
            return "LEFT_CLICK"

        # --------------------------------------------------
        # Right Click
        # Thumb + Middle Pinch
        # --------------------------------------------------

        if self.pinch.thumb_middle(landmarks):
            return "RIGHT_CLICK"

        # --------------------------------------------------
        # Mouse Move
        # Only Index Finger
        # --------------------------------------------------

        if states == [0, 1, 0, 0, 0]:
            return "MOVE"

        # --------------------------------------------------
        # Drag
        # Index + Middle
        # --------------------------------------------------

        if states == [0, 1, 1, 0, 0]:
            return "DRAG"

        # --------------------------------------------------
        # Scroll
        # Middle Finger Only
        # --------------------------------------------------

        if states == [0, 0, 1, 0, 0]:
            return "SCROLL"

        return "IDLE"