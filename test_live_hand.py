import cv2

from core.hand_tracker import HandTracker
from core.gesture_detector import GestureDetector


hand_tracker = HandTracker()
gesture_detector = GestureDetector()

camera = cv2.VideoCapture(0)

print("Live hand test started.")
print("Press Q inside the camera window to quit.")


while True:

    success, frame = camera.read()

    if not success:
        print("Could not read camera frame.")
        break

    data = hand_tracker.detect(frame)

    results = data.get("results")

    frame = hand_tracker.draw_landmarks(
        frame,
        results
    )

    gesture = gesture_detector.detect(data)

    hand_detected = data.get(
        "hand_detected",
        False
    )

    gesture_name = gesture.get(
        "gesture",
        "NONE"
    )

    confidence = data.get(
        "confidence",
        0.0
    )

    cv2.putText(
        frame,
        f"Hand: {hand_detected}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Gesture: {gesture_name}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Confidence: {confidence:.2f}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow(
        "AI Virtual Mouse - Hand Test",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


camera.release()

hand_tracker.close()

cv2.destroyAllWindows()

print("Live hand test ended.")