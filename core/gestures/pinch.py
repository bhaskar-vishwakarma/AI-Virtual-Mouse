"""
pinch.py
---------
Pinch gesture detection utilities.

Detects the distance between the thumb and other fingertips.
"""

from __future__ import annotations

from math import hypot
from typing import Dict


class PinchDetector:
    """
    Utility class for detecting pinch gestures.
    """

    # Landmark IDs
    THUMB = 4
    INDEX = 8
    MIDDLE = 12
    RING = 16
    PINKY = 20

    def __init__(self, threshold: float = 40.0):
        """
        Parameters
        ----------
        threshold : float
            Maximum pixel distance to consider a pinch.
        """
        self.threshold = threshold

    # ==========================================================
    # Distance
    # ==========================================================

    @staticmethod
    def distance(point1: Dict, point2: Dict) -> float:
        """
        Euclidean distance between two landmarks.
        """
        return hypot(
            point2["x"] - point1["x"],
            point2["y"] - point1["y"]
        )

    # ==========================================================
    # Generic Pinch
    # ==========================================================

    def is_pinch(
        self,
        landmarks: list,
        finger_tip: int
    ) -> bool:
        """
        Check whether thumb is pinching another fingertip.
        """
        thumb = landmarks[self.THUMB]
        finger = landmarks[finger_tip]

        return self.distance(thumb, finger) <= self.threshold

    # ==========================================================
    # Convenience Methods
    # ==========================================================

    def thumb_index(self, landmarks: list) -> bool:
        return self.is_pinch(landmarks, self.INDEX)

    def thumb_middle(self, landmarks: list) -> bool:
        return self.is_pinch(landmarks, self.MIDDLE)

    def thumb_ring(self, landmarks: list) -> bool:
        return self.is_pinch(landmarks, self.RING)

    def thumb_pinky(self, landmarks: list) -> bool:
        return self.is_pinch(landmarks, self.PINKY)

    # ==========================================================
    # Pinch Distance
    # ==========================================================

    def pinch_distance(
        self,
        landmarks: list,
        finger_tip: int = INDEX
    ) -> float:
        """
        Returns the raw pinch distance.

        Useful for:
        - Volume
        - Brightness
        - Zoom
        """
        return self.distance(
            landmarks[self.THUMB],
            landmarks[finger_tip]
        )