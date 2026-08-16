"""
presentation.py
---------------
Presentation control gestures.
"""

from __future__ import annotations

from .finger_state import get_finger_state


def detect_presentation_gesture(hand_data):
    fingers = get_finger_state(hand_data)

    if fingers == [0, 1, 0, 0, 0]:
        return "NEXT_SLIDE", 0.95

    if fingers == [0, 1, 1, 0, 0]:
        return "PREVIOUS_SLIDE", 0.95

    if fingers == [1, 1, 1, 1, 1]:
        return "START_PRESENTATION", 0.95

    if fingers == [0, 0, 0, 0, 0]:
        return "END_PRESENTATION", 0.95

    return "UNKNOWN", 0.50