"""
gesture_detector.py
-------------------
Reliable hand gesture recognition using MediaPipe hand landmarks.

This class ONLY detects gestures.
Actual mouse, keyboard, window, and system actions belong to controllers.
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple


class GestureDetector:
    """
    Detects hand gestures from MediaPipe landmark data.

    Supported gestures:
        NONE
        OPEN_PALM
        FIST
        INDEX
        TWO_FINGER
        THUMB_UP
        PINCH
        OK

    Media gestures (reserved for MediaController):
        FOUR_FINGER     index + middle + ring + pinky
        THREE_FINGER    index + middle + ring
        ROCK            index + pinky
        CALL            thumb + pinky
        PINKY           pinky only
        THUMB_DOWN      thumb only, pointing downward
    """

    # ============================================================
    # MEDIAPIPE LANDMARK INDEXES
    # ============================================================

    WRIST = 0

    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(
        self,
        history_size: int = 7,
        stable_frames: int = 4,
        pinch_threshold: float = 0.42,
    ):
        self.history_size = max(3, history_size)
        self.stable_frames = max(2, stable_frames)
        self.pinch_threshold = float(pinch_threshold)

        self.gesture_history = deque(
            maxlen=self.history_size
        )

        self.last_gesture = "NONE"
        self.stable_gesture = "NONE"

        self.position_history = deque(
            maxlen=8
        )

        self.last_detection_time = 0.0

    # ============================================================
    # PUBLIC API
    # ============================================================

    def detect(
        self,
        hand_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Detect the strongest gesture from hand tracker output.
        """

        default_result = self._empty_result()

        if not isinstance(hand_data, dict):
            self._reset_tracking()
            return default_result

        hands = hand_data.get(
            "hands",
            [],
        )

        if not isinstance(hands, list) or not hands:
            self._reset_tracking()
            return default_result

        hand = self._select_best_hand(
            hands
        )

        if hand is None:
            self._reset_tracking()
            return default_result

        landmarks = self._extract_landmarks(
            hand
        )

        if len(landmarks) < 21:
            self._reset_tracking()
            return default_result

        handedness = self._extract_handedness(
            hand
        )

        confidence = self._extract_confidence(
            hand
        )

        fingers = self._finger_state(
            landmarks,
            handedness,
        )

        pinch = self._pinch_state(
            landmarks
        )

        position = self._point(
            landmarks,
            self.INDEX_TIP,
        )

        self._update_position_history(
            position
        )

        motion = self._motion_state()

        gesture = self._classify_gesture(
            fingers=fingers,
            pinch=pinch,
            landmarks=landmarks,
        )

        stable = self._update_stability(
            gesture
        )

        self.last_detection_time = time.time()

        return {
            "gesture": gesture,
            "stable": stable,
            "confidence": confidence,
            "hand_detected": True,
            "handedness": handedness,
            "landmarks": landmarks,
            "fingers": fingers,
            "pinch": pinch,
            "position": position,
            "motion": motion,
        }

    def get_last_gesture(self) -> str:
        return self.last_gesture

    def get_gesture_history(self) -> List[str]:
        return list(
            self.gesture_history
        )

    def reset(self) -> None:
        self._reset_tracking()

    # ============================================================
    # HAND SELECTION
    # ============================================================

    def _select_best_hand(
        self,
        hands: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Select the hand with the highest confidence.

        Supports:

            [
                {
                    "landmarks": [...],
                    "confidence": 0.9
                }
            ]

        and:

            [
                [landmark1, landmark2, ...]
            ]
        """

        if not isinstance(hands, list):
            return None

        if not hands:
            return None

        normalized = []

        for item in hands:

            if isinstance(item, dict):
                normalized.append(item)
                continue

            if isinstance(item, list):
                normalized.append(
                    {
                        "landmarks": item,
                        "confidence": 1.0,
                        "handedness": "Unknown",
                    }
                )

        if not normalized:
            return None

        return max(
            normalized,
            key=lambda item: self._extract_confidence(
                item
            ),
        )

    # ============================================================
    # LANDMARK EXTRACTION
    # ============================================================

    def _extract_landmarks(
        self,
        hand: Dict[str, Any],
    ) -> List[Any]:

        if not isinstance(hand, dict):
            return []

        landmarks = hand.get(
            "landmarks",
            [],
        )

        if isinstance(landmarks, list):
            return landmarks

        return []

    def _extract_handedness(
        self,
        hand: Dict[str, Any],
    ) -> str:

        if not isinstance(hand, dict):
            return "Unknown"

        value = hand.get(
            "handedness",
            "Unknown",
        )

        if isinstance(value, str):
            return value

        if isinstance(value, list) and value:

            first = value[0]

            if isinstance(first, dict):
                return str(
                    first.get(
                        "category_name",
                        first.get(
                            "display_name",
                            "Unknown",
                        ),
                    )
                )

            return str(first)

        if isinstance(value, dict):
            return str(
                value.get(
                    "category_name",
                    value.get(
                        "display_name",
                        "Unknown",
                    ),
                )
            )

        return "Unknown"

    def _extract_confidence(
        self,
        hand: Dict[str, Any],
    ) -> float:

        if not isinstance(hand, dict):
            return 0.0

        confidence = hand.get(
            "confidence",
            hand.get(
                "score",
                hand.get(
                    "hand_confidence",
                    0.0,
                ),
            ),
        )

        try:
            return float(confidence)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    # ============================================================
    # LANDMARK HELPERS
    # ============================================================

    def _xyz(
        self,
        landmark: Any,
    ) -> Tuple[float, float, float]:
        """
        Safely extract x/y/z from a MediaPipe landmark.
        """

        if isinstance(landmark, dict):

            try:
                x = float(
                    landmark.get(
                        "x",
                        0.0,
                    )
                )

                y = float(
                    landmark.get(
                        "y",
                        0.0,
                    )
                )

                z = float(
                    landmark.get(
                        "z",
                        0.0,
                    )
                )

                return x, y, z

            except (
                TypeError,
                ValueError,
            ):
                return 0.0, 0.0, 0.0

        try:
            x = float(
                getattr(
                    landmark,
                    "x",
                    0.0,
                )
            )

            y = float(
                getattr(
                    landmark,
                    "y",
                    0.0,
                )
            )

            z = float(
                getattr(
                    landmark,
                    "z",
                    0.0,
                )
            )

            return x, y, z

        except (
            TypeError,
            ValueError,
        ):
            return 0.0, 0.0, 0.0

    def _point(
        self,
        landmarks: List[Any],
        index: int,
    ) -> Optional[Tuple[float, float]]:

        if len(landmarks) <= index:
            return None

        x, y, _ = self._xyz(
            landmarks[index]
        )

        return x, y

    def _distance_points(
        self,
        a: Tuple[float, float, float],
        b: Tuple[float, float, float],
    ) -> float:

        return math.sqrt(
            (a[0] - b[0]) ** 2
            + (a[1] - b[1]) ** 2
            + (a[2] - b[2]) ** 2
        )

    def _distance(
        self,
        landmarks: List[Any],
        index_a: int,
        index_b: int,
    ) -> float:

        if len(landmarks) <= max(
            index_a,
            index_b,
        ):
            return 999.0

        a = self._xyz(
            landmarks[index_a]
        )

        b = self._xyz(
            landmarks[index_b]
        )

        return self._distance_points(
            a,
            b,
        )

    def _angle(
        self,
        a: Tuple[float, float, float],
        b: Tuple[float, float, float],
        c: Tuple[float, float, float],
    ) -> float:
        """
        Returns angle ABC in degrees.
        """

        ba = (
            a[0] - b[0],
            a[1] - b[1],
            a[2] - b[2],
        )

        bc = (
            c[0] - b[0],
            c[1] - b[1],
            c[2] - b[2],
        )

        magnitude_ba = math.sqrt(
            ba[0] ** 2
            + ba[1] ** 2
            + ba[2] ** 2
        )

        magnitude_bc = math.sqrt(
            bc[0] ** 2
            + bc[1] ** 2
            + bc[2] ** 2
        )

        if (
            magnitude_ba < 1e-6
            or magnitude_bc < 1e-6
        ):
            return 0.0

        dot = (
            ba[0] * bc[0]
            + ba[1] * bc[1]
            + ba[2] * bc[2]
        )

        cosine = dot / (
            magnitude_ba
            * magnitude_bc
        )

        cosine = max(
            -1.0,
            min(
                1.0,
                cosine,
            ),
        )

        return math.degrees(
            math.acos(cosine)
        )

    # ============================================================
    # FINGER DETECTION
    # ============================================================

    def _finger_state(
        self,
        landmarks: List[Any],
        handedness: str = "Unknown",
    ) -> Dict[str, bool]:

        thumb = self._is_thumb_extended(
            landmarks,
            handedness,
        )

        index = self._is_finger_extended(
            landmarks,
            self.INDEX_MCP,
            self.INDEX_PIP,
            self.INDEX_DIP,
            self.INDEX_TIP,
        )

        middle = self._is_finger_extended(
            landmarks,
            self.MIDDLE_MCP,
            self.MIDDLE_PIP,
            self.MIDDLE_DIP,
            self.MIDDLE_TIP,
        )

        ring = self._is_finger_extended(
            landmarks,
            self.RING_MCP,
            self.RING_PIP,
            self.RING_DIP,
            self.RING_TIP,
        )

        pinky = self._is_finger_extended(
            landmarks,
            self.PINKY_MCP,
            self.PINKY_PIP,
            self.PINKY_DIP,
            self.PINKY_TIP,
        )

        return {
            "thumb": thumb,
            "index": index,
            "middle": middle,
            "ring": ring,
            "pinky": pinky,
        }

    def _is_finger_extended(
        self,
        landmarks: List[Any],
        mcp: int,
        pip: int,
        dip: int,
        tip: int,
    ) -> bool:
        """
        Detect extended fingers using joint angles plus
        distance from the wrist.

        This avoids relying only on X/Y orientation.
        """

        if len(landmarks) < 21:
            return False

        mcp_point = self._xyz(
            landmarks[mcp]
        )

        pip_point = self._xyz(
            landmarks[pip]
        )

        dip_point = self._xyz(
            landmarks[dip]
        )

        tip_point = self._xyz(
            landmarks[tip]
        )

        wrist_point = self._xyz(
            landmarks[self.WRIST]
        )

        pip_angle = self._angle(
            mcp_point,
            pip_point,
            dip_point,
        )

        dip_angle = self._angle(
            pip_point,
            dip_point,
            tip_point,
        )

        wrist_to_tip = self._distance_points(
            wrist_point,
            tip_point,
        )

        wrist_to_pip = self._distance_points(
            wrist_point,
            pip_point,
        )

        # Straight finger.
        straight_enough = (
            pip_angle >= 145.0
            and dip_angle >= 145.0
        )

        # Tip must also be farther from wrist
        # than the PIP joint.
        extended_from_wrist = (
            wrist_to_tip
            > wrist_to_pip * 1.08
        )

        return (
            straight_enough
            and extended_from_wrist
        )

    def _is_thumb_extended(
        self,
        landmarks: List[Any],
        handedness: str = "Unknown",
    ) -> bool:
        """
        Detect whether the thumb is extended.

        The thumb is different from the four fingers because
        it moves sideways across the palm. We therefore use
        thumb joint angles and palm distance rather than only
        comparing Y coordinates.
        """

        if len(landmarks) < 21:
            return False

        cmc = self._xyz(
            landmarks[self.THUMB_CMC]
        )

        mcp = self._xyz(
            landmarks[self.THUMB_MCP]
        )

        ip = self._xyz(
            landmarks[self.THUMB_IP]
        )

        tip = self._xyz(
            landmarks[self.THUMB_TIP]
        )

        wrist = self._xyz(
            landmarks[self.WRIST]
        )

        index_mcp = self._xyz(
            landmarks[self.INDEX_MCP]
        )

        middle_mcp = self._xyz(
            landmarks[self.MIDDLE_MCP]
        )

        # Thumb joint angles.
        mcp_angle = self._angle(
            cmc,
            mcp,
            ip,
        )

        ip_angle = self._angle(
            mcp,
            ip,
            tip,
        )

        # Thumb should be relatively straight.
        straight_thumb = (
            mcp_angle >= 125.0
            and ip_angle >= 135.0
        )

        # Distances from palm/wrist.
        wrist_to_tip = self._distance_points(
            wrist,
            tip,
        )

        wrist_to_ip = self._distance_points(
            wrist,
            ip,
        )

        index_to_tip = self._distance_points(
            index_mcp,
            tip,
        )

        index_to_ip = self._distance_points(
            index_mcp,
            ip,
        )

        middle_to_tip = self._distance_points(
            middle_mcp,
            tip,
        )

        middle_to_ip = self._distance_points(
            middle_mcp,
            ip,
        )

        # Thumb tip must be noticeably farther out.
        wrist_extension = (
            wrist_to_tip
            > wrist_to_ip * 1.08
        )

        palm_extension = (
            index_to_tip
            > index_to_ip * 1.08
            or
            middle_to_tip
            > middle_to_ip * 1.08
        )

        # Additional thumb-tip separation from index MCP.
        thumb_sideways = (
            index_to_tip > 0.13
            or middle_to_tip > 0.16
        )

        return (
            straight_thumb
            and wrist_extension
            and palm_extension
            and thumb_sideways
        )

    # ============================================================
    # PINCH DETECTION
    # ============================================================

    def _is_thumb_down(
        self,
        landmarks: List[Any],
    ) -> bool:
        """
        Return True when an extended thumb points downward.

        MediaPipe y grows towards the bottom of the frame, so a
        thumb tip sitting below both its own MCP joint and the
        wrist is treated as THUMB_DOWN.
        """

        if len(landmarks) <= self.PINKY_TIP:
            return False

        try:

            _, tip_y, _ = self._xyz(
                landmarks[self.THUMB_TIP]
            )

            _, mcp_y, _ = self._xyz(
                landmarks[self.THUMB_MCP]
            )

            _, wrist_y, _ = self._xyz(
                landmarks[self.WRIST]
            )

        except (
            IndexError,
            TypeError,
            ValueError,
        ):
            return False

        return (
            tip_y > mcp_y
            and tip_y > wrist_y
        )

    def _pinch_state(
        self,
        landmarks: List[Any],
    ) -> Dict[str, Any]:

        if len(landmarks) < 21:
            return {
                "index": False,
                "middle": False,
                "index_distance": 999.0,
                "middle_distance": 999.0,
            }

        index_distance = self._distance(
            landmarks,
            self.THUMB_TIP,
            self.INDEX_TIP,
        )

        middle_distance = self._distance(
            landmarks,
            self.THUMB_TIP,
            self.MIDDLE_TIP,
        )

        # Use palm size for scale normalization.
        hand_size = self._distance(
            landmarks,
            self.WRIST,
            self.MIDDLE_MCP,
        )

        if hand_size <= 1e-6:
            hand_size = 0.1

        normalized_index = (
            index_distance / hand_size
        )

        normalized_middle = (
            middle_distance / hand_size
        )

        index_pinch = (
            normalized_index
            < self.pinch_threshold
        )

        middle_pinch = (
            normalized_middle
            < self.pinch_threshold
        )

        return {
            "index": index_pinch,
            "middle": middle_pinch,
            "index_distance": round(
                normalized_index,
                3,
            ),
            "middle_distance": round(
                normalized_middle,
                3,
            ),
        }

    # ============================================================
    # GESTURE CLASSIFICATION
    # ============================================================

    def _classify_gesture(
        self,
        fingers: Dict[str, bool],
        pinch: Dict[str, Any],
        landmarks: List[Any],
    ) -> str:

        thumb = bool(
            fingers.get(
                "thumb",
                False,
            )
        )

        index = bool(
            fingers.get(
                "index",
                False,
            )
        )

        middle = bool(
            fingers.get(
                "middle",
                False,
            )
        )

        ring = bool(
            fingers.get(
                "ring",
                False,
            )
        )

        pinky = bool(
            fingers.get(
                "pinky",
                False,
            )
        )

        index_pinch = bool(
            pinch.get(
                "index",
                False,
            )
        )

        middle_pinch = bool(
            pinch.get(
                "middle",
                False,
            )
        )

        # ========================================================
        # 1. OK
        # ========================================================

        if (
            index_pinch
            and middle
            and ring
            and pinky
        ):
            return "OK"

        # ========================================================
        # 2. PINCH
        # ========================================================

        if (
            index_pinch
            and not middle_pinch
        ):
            return "PINCH"

        # ========================================================
        # 3. OPEN PALM
        # ========================================================

        if (
            thumb
            and index
            and middle
            and ring
            and pinky
        ):
            return "OPEN_PALM"

        # ========================================================
        # 4. FOUR FINGER  (media: volume up)
        # ========================================================

        if (
            not thumb
            and index
            and middle
            and ring
            and pinky
        ):
            return "FOUR_FINGER"

        # ========================================================
        # 5. THREE FINGER  (media: play / pause)
        # ========================================================

        if (
            index
            and middle
            and ring
            and not pinky
        ):
            return "THREE_FINGER"

        # ========================================================
        # 6. ROCK  (media: next track)
        # ========================================================

        if (
            not thumb
            and index
            and not middle
            and not ring
            and pinky
        ):
            return "ROCK"

        # ========================================================
        # 7. CALL  (media: previous track)
        # ========================================================

        if (
            thumb
            and not index
            and not middle
            and not ring
            and pinky
        ):
            return "CALL"

        # ========================================================
        # 8. PINKY  (media: volume down)
        # ========================================================

        if (
            not thumb
            and not index
            and not middle
            and not ring
            and pinky
        ):
            return "PINKY"

        # ========================================================
        # 9. THUMB DOWN  (media: mute)
        # ========================================================

        if (
            thumb
            and not index
            and not middle
            and not ring
            and not pinky
            and self._is_thumb_down(landmarks)
        ):
            return "THUMB_DOWN"

        # ========================================================
        # 10. THUMB UP
        # ========================================================

        if (
            thumb
            and not index
            and not middle
            and not ring
            and not pinky
        ):
            return "THUMB_UP"

        # ========================================================
        # 11. INDEX
        # ========================================================

        if (
            index
            and not middle
            and not ring
            and not pinky
        ):
            return "INDEX"

        # ========================================================
        # 12. TWO FINGER
        # ========================================================

        if (
            index
            and middle
            and not ring
            and not pinky
        ):
            return "TWO_FINGER"

        # ========================================================
        # 13. FIST
        # ========================================================

        if (
            not thumb
            and not index
            and not middle
            and not ring
            and not pinky
        ):
            return "FIST"

        return "NONE"

    # ============================================================
    # STABILITY
    # ============================================================

    def _update_stability(
        self,
        gesture: str,
    ) -> bool:

        self.gesture_history.append(
            gesture
        )

        self.last_gesture = gesture

        if (
            len(self.gesture_history)
            < self.stable_frames
        ):
            return False

        recent = list(
            self.gesture_history
        )[-self.stable_frames:]

        if all(
            item == gesture
            for item in recent
        ):
            self.stable_gesture = gesture
            return True

        return False

    # ============================================================
    # POSITION TRACKING
    # ============================================================

    def _update_position_history(
        self,
        position: Optional[
            Tuple[float, float]
        ],
    ) -> None:

        if position is None:
            return

        self.position_history.append(
            position
        )

    # ============================================================
    # MOTION
    # ============================================================

    def _motion_state(self) -> Dict[str, Any]:
        """
        Derive a motion vector from the tracked index-tip history.

        Coordinates are MediaPipe normalized values, so dx/dy are
        fractions of the frame and comparable across resolutions.

        Returns:

        {
            "dx": float,          # + right
            "dy": float,          # + down
            "speed": float,       # magnitude of (dx, dy)
            "axis": str,          # "HORIZONTAL" / "VERTICAL" / "NONE"
            "direction": str,     # LEFT/RIGHT/UP/DOWN/NONE
        }
        """

        empty = {
            "dx": 0.0,
            "dy": 0.0,
            "speed": 0.0,
            "axis": "NONE",
            "direction": "NONE",
        }

        if len(self.position_history) < 2:
            return empty

        try:

            start_x, start_y = (
                self.position_history[0]
            )

            end_x, end_y = (
                self.position_history[-1]
            )

        except (
            TypeError,
            ValueError,
        ):
            return empty

        dx = float(end_x) - float(start_x)
        dy = float(end_y) - float(start_y)

        speed = math.sqrt(
            dx * dx
            + dy * dy
        )

        if abs(dx) >= abs(dy):

            axis = "HORIZONTAL"

            direction = (
                "RIGHT"
                if dx > 0
                else "LEFT"
            )

        else:

            axis = "VERTICAL"

            direction = (
                "DOWN"
                if dy > 0
                else "UP"
            )

        return {
            "dx": dx,
            "dy": dy,
            "speed": speed,
            "axis": axis,
            "direction": direction,
        }

    # ============================================================
    # RESET
    # ============================================================

    def _reset_tracking(self) -> None:

        self.gesture_history.clear()
        self.position_history.clear()

        self.last_gesture = "NONE"
        self.stable_gesture = "NONE"

    # ============================================================
    # DEFAULT RESULT
    # ============================================================

    def _empty_result(
        self,
    ) -> Dict[str, Any]:

        return {
            "gesture": "NONE",
            "stable": False,
            "confidence": 0.0,
            "hand_detected": False,
            "handedness": "Unknown",
            "landmarks": [],
            "fingers": {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False,
            },
            "pinch": {
                "index": False,
                "middle": False,
                "index_distance": 0.0,
                "middle_distance": 0.0,
            },
            "position": None,
            "motion": {
                "dx": 0.0,
                "dy": 0.0,
                "speed": 0.0,
                "axis": "NONE",
                "direction": "NONE",
            },
        }