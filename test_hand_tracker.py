import cv2

from core.hand_tracker import HandTracker


cap = cv2.VideoCapture(0)

tracker = HandTracker()


while True:

    success, frame = cap.read()

    if not success:
        break


    results = tracker.process(frame)


    tracker.draw(
        frame,
        results
    )


    cv2.imshow(
        "Hand Tracker Test",
        frame
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()