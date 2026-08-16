"""
hand_utils.py
-------------
Utility functions for hand tracking and gesture recognition.
"""

from __future__ import annotations

import math
from typing import List, Tuple

Point = Tuple[int, int]


class HandUtils:
    """
    Collection of helper methods for hand tracking.
    """

    @staticmethod
    def distance(point1: Point, point2: Point) -> float:
        """
        Calculate Euclidean distance between two points.
        """
        return math.hypot(
            point2[0] - point1[0],
            point2[1] - point1[1]
        )

    @staticmethod
    def midpoint(point1: Point, point2: Point) -> Point:
        """
        Calculate midpoint between two points.
        """
        return (
            (point1[0] + point2[0]) // 2,
            (point1[1] + point2[1]) // 2
        )

    @staticmethod
    def calculate_center(points: List[Point]) -> Point:
        """
        Calculate center of a list of points.
        """
        if not points:
            return (0, 0)

        x = sum(p[0] for p in points) // len(points)
        y = sum(p[1] for p in points) // len(points)

        return (x, y)

    @staticmethod
    def bounding_box(points: List[Point]) -> Tuple[int, int, int, int]:
        """
        Calculate bounding rectangle.
        Returns (x, y, width, height)
        """
        if not points:
            return (0, 0, 0, 0)

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x = min(xs)
        y = min(ys)

        width = max(xs) - x
        height = max(ys) - y

        return (x, y, width, height)

    @staticmethod
    def angle(point1: Point, point2: Point, point3: Point) -> float:
        """
        Calculate angle (in degrees) formed by three points.
        """

        a = (
            point1[0] - point2[0],
            point1[1] - point2[1]
        )

        b = (
            point3[0] - point2[0],
            point3[1] - point2[1]
        )

        dot = a[0] * b[0] + a[1] * b[1]

        mag_a = math.hypot(*a)
        mag_b = math.hypot(*b)

        if mag_a == 0 or mag_b == 0:
            return 0.0

        cosine = dot / (mag_a * mag_b)
        cosine = max(-1.0, min(1.0, cosine))

        return math.degrees(math.acos(cosine))