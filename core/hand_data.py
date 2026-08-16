"""
hand_data.py
------------
Dataclass representing all information about a detected hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


Point = Tuple[int, int]
BoundingBox = Tuple[int, int, int, int]


@dataclass
class HandData:
    """
    Stores all information about a detected hand.
    """

    # Hand landmarks (21 points)
    landmarks: List[Point] = field(default_factory=list)

    # Right or Left
    handedness: str = "Unknown"

    # Detection confidence
    confidence: float = 0.0

    # Finger state
    # Example: [1,1,0,0,0]
    fingers: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])

    # Bounding rectangle
    bounding_box: Optional[BoundingBox] = None

    # Center of hand
    center: Optional[Point] = None

    # Distance between thumb & index
    pinch_distance: float = 0.0

    # Palm size
    palm_width: float = 0.0
    palm_height: float = 0.0

    # Gesture name
    gesture: str = "None"

    # Tracking state
    detected: bool = False