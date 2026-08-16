from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:
    """
    MediaPipe Tasks based hand tracker.

    Produces hand data compatible with GestureDetector.
    """

    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7,
        model_path: Optional[str] = None,
    ):
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent
            model_path = (
                project_root
                / "models"
                / "hand_landmarker.task"
            )

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Hand Landmarker model not found: "
                f"{self.model_path}"
            )

        base_options = python.BaseOptions(
            model_asset_path=str(self.model_path)
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        self.landmarker = vision.HandLandmarker.create_from_options(
            options
        )

        self.last_result = None

    # ==========================================================
    # Detect
    # ==========================================================

    def detect(self, frame) -> Dict[str, Any]:

        if frame is None:
            return self._empty_data()

        try:
            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )

            result = self.landmarker.detect(mp_image)

            self.last_result = result

            hands = []
            all_landmarks = []
            handedness_list = []

            if result.hand_landmarks:

                for hand_index, hand in enumerate(
                    result.hand_landmarks
                ):

                    landmarks = []

                    for landmark_id, landmark in enumerate(hand):

                        landmarks.append(
                            {
                                "id": landmark_id,
                                "x": float(landmark.x),
                                "y": float(landmark.y),
                                "z": float(landmark.z),
                            }
                        )

                    confidence = 0.0
                    handedness = "Unknown"

                    if (
                        result.handedness
                        and hand_index < len(result.handedness)
                        and result.handedness[hand_index]
                    ):
                        category = result.handedness[
                            hand_index
                        ][0]

                        confidence = float(
                            category.score or 0.0
                        )

                        handedness = (
                            category.category_name
                            or "Unknown"
                        )

                    # IMPORTANT:
                    # GestureDetector expects each hand
                    # to be a dictionary.
                    hands.append(
                        {
                            "landmarks": landmarks,
                            "confidence": confidence,
                            "handedness": handedness,
                        }
                    )

                    all_landmarks.append(landmarks)
                    handedness_list.append(handedness)

            confidence = 0.0

            if hands:
                confidence = hands[0]["confidence"]

            return {
                "results": result,

                # GestureDetector uses this.
                "hands": hands,

                "handedness": (
                    handedness_list[0]
                    if handedness_list
                    else "Unknown"
                ),

                "landmarks": all_landmarks,

                "hand_detected": bool(hands),

                "confidence": confidence,
            }

        except Exception as e:

            print(
                f"[HandTracker] Detection error: {e}"
            )

            return self._empty_data()

    # ==========================================================
    # Empty Data
    # ==========================================================

    def _empty_data(self) -> Dict[str, Any]:

        return {
            "results": None,
            "hands": [],
            "handedness": "Unknown",
            "landmarks": [],
            "hand_detected": False,
            "confidence": 0.0,
        }

    # ==========================================================
    # Process
    # ==========================================================

    def process(self, frame):

        data = self.detect(frame)

        return data

    # ==========================================================
    # Draw Landmarks
    # ==========================================================

    def draw_landmarks(
        self,
        frame,
        results=None,
    ):

        if frame is None:
            return frame

        if results is None:
            return frame

        try:

            height, width = frame.shape[:2]

            if not results.hand_landmarks:
                return frame

            connections = [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),

                (0, 5),
                (5, 6),
                (6, 7),
                (7, 8),

                (0, 9),
                (9, 10),
                (10, 11),
                (11, 12),

                (0, 13),
                (13, 14),
                (14, 15),
                (15, 16),

                (0, 17),
                (17, 18),
                (18, 19),
                (19, 20),

                (5, 9),
                (9, 13),
                (13, 17),
            ]

            for hand in results.hand_landmarks:

                points = []

                for landmark in hand:

                    x = int(landmark.x * width)
                    y = int(landmark.y * height)

                    points.append((x, y))

                    cv2.circle(
                        frame,
                        (x, y),
                        4,
                        (255, 255, 255),
                        -1,
                    )

                for start, end in connections:

                    if (
                        start < len(points)
                        and end < len(points)
                    ):

                        cv2.line(
                            frame,
                            points[start],
                            points[end],
                            (255, 255, 255),
                            2,
                        )

            return frame

        except Exception as e:

            print(
                f"[HandTracker] Drawing error: {e}"
            )

            return frame

    # ==========================================================
    # Get Landmarks
    # ==========================================================

    def get_landmarks(
        self,
        frame,
    ) -> List[List[Dict[str, Any]]]:

        data = self.detect(frame)

        return data.get(
            "landmarks",
            [],
        )

    # ==========================================================
    # Close
    # ==========================================================

    def close(self):

        if self.landmarker is not None:

            try:
                self.landmarker.close()
            except Exception:
                pass

            self.landmarker = None

        self.last_result = None