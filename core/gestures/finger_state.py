"""
finger_state.py
---------------
Determines which fingers are extended.

Returns finger states in the order:

[Thumb, Index, Middle, Ring, Pinky]

1 = Extended
0 = Folded
"""

from __future__ import annotations

from typing import List


class FingerState:
    """
    Utility class for determining finger states.
    """

    # Landmark indices
    THUMB_TIP = 4
    THUMB_IP = 3

    INDEX_TIP = 8
    INDEX_PIP = 6

    MIDDLE_TIP = 12
    MIDDLE_PIP = 10

    RING_TIP = 16
    RING_PIP = 14

    PINKY_TIP = 20
    PINKY_PIP = 18

    def __init__(self):
        pass

    # ==========================================================
    # Public API
    # ==========================================================

    def get_states(
        self,
        landmarks: list,
        hand_type: str = "Right"
    ) -> List[int]:
        """
        Returns finger states.

        Parameters
        ----------
        landmarks : list
            List of 21 landmark dictionaries.

        hand_type : str
            "Right" or "Left"

        Returns
        -------
        list[int]

        Example
        -------
        [0,1,1,0,0]
        """

        if len(landmarks) != 21:
            return [0, 0, 0, 0, 0]

        thumb = self._thumb_state(
            landmarks,
            hand_type
        )

        index = self._finger_state(
            landmarks,
            self.INDEX_TIP,
            self.INDEX_PIP
        )

        middle = self._finger_state(
            landmarks,
            self.MIDDLE_TIP,
            self.MIDDLE_PIP
        )

        ring = self._finger_state(
            landmarks,
            self.RING_TIP,
            self.RING_PIP
        )

        pinky = self._finger_state(
            landmarks,
            self.PINKY_TIP,
            self.PINKY_PIP
        )

        return [
            thumb,
            index,
            middle,
            ring,
            pinky
        ]

    # ==========================================================
    # Private
    # ==========================================================

    def _finger_state(
        self,
        landmarks,
        tip,
        pip
    ) -> int:
        """
        Finger is open if TIP is above PIP.
        """

        if landmarks[tip]["y"] < landmarks[pip]["y"]:
            return 1

        return 0

    def _thumb_state(
        self,
        landmarks,
        hand_type
    ) -> int:
        """
        Thumb detection depends on left/right hand.
        """

        thumb_tip = landmarks[self.THUMB_TIP]["x"]
        thumb_ip = landmarks[self.THUMB_IP]["x"]

        if hand_type == "Right":
            return int(thumb_tip > thumb_ip)

        return int(thumb_tip < thumb_ip)

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def count(states: List[int]) -> int:
        """
        Count extended fingers.
        """

        return sum(states)

    @staticmethod
    def is_only(
        states: List[int],
        finger_index: int
    ) -> bool:
        """
        Returns True if only one finger is extended.

        finger_index

        0 Thumb
        1 Index
        2 Middle
        3 Ring
        4 Pinky
        """

        return (
            states[finger_index] == 1
            and sum(states) == 1
        )

    @staticmethod
    def all_open(states: List[int]) -> bool:
        """
        All fingers extended.
        """

        return sum(states) == 5

    @staticmethod
    def fist(states: List[int]) -> bool:
        """
        Closed fist.
        """

        return sum(states) == 0