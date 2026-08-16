"""
media.py
--------
Media control gestures.
"""

from __future__ import annotations

from .finger_state import get_finger_state


def detect_media_gesture(hand_data):
    fingers = get_finger_state(hand_data)

    if fingers == [0, 1, 1, 1, 1]:
        return "VOLUME_UP", 0.95

    if fingers == [1, 0, 0, 0, 0]:
        return "VOLUME_DOWN", 0.95

    if fingers == [0, 1, 1, 0, 0]:
        return "PLAY_PAUSE", 0.95

    return "UNKNOWN", 0.50