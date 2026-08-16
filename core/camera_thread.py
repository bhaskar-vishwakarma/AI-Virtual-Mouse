"""
camera_thread.py
----------------
Dedicated webcam capture thread.

Responsibilities:
- Open webcam
- Capture frames continuously
- Calculate FPS
- Emit frames to UI
- Handle camera failures
- Graceful shutdown
"""

from __future__ import annotations

import time
import cv2

from PyQt6.QtCore import QThread, pyqtSignal


class CameraThread(QThread):
    """
    Dedicated thread for webcam capture.
    """

    # ==============================
    # Signals
    # ==============================

    frame_ready = pyqtSignal(object)
    fps_updated = pyqtSignal(float)
    camera_status = pyqtSignal(bool)

    # ==============================

    def __init__(
        self,
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        parent=None,
    ):
        super().__init__(parent)

        self.camera_index = camera_index
        self.width = width
        self.height = height

        self.cap = None
        self.running = False

        self.previous_time = time.perf_counter()

    # ===================================================
    # Camera Initialization
    # ===================================================

    def initialize_camera(self) -> bool:
        """
        Open webcam and configure properties.
        """

        # CAP_DSHOW improves startup speed on Windows.
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            self.camera_status.emit(False)
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Reduce latency by minimizing internal buffering.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.camera_status.emit(True)
        return True

    # ===================================================
    # Main Thread
    # ===================================================

    def run(self):
        """
        Main camera capture loop.
        """

        if not self.initialize_camera():
            return

        self.running = True
        self.previous_time = time.perf_counter()

        try:

            while self.running:

                success, frame = self.cap.read()

                if not success:
                    self.camera_status.emit(False)
                    self.msleep(10)
                    continue

                frame = cv2.flip(frame, 1)

                current = time.perf_counter()
                delta = current - self.previous_time
                self.previous_time = current

                fps = (1.0 / delta) if delta > 0 else 0.0

                self.fps_updated.emit(round(fps, 1))
                self.frame_ready.emit(frame)

        except Exception as e:
            print(f"[CameraThread] {e}")

        finally:
            self.release_camera()

    # ===================================================
    # Stop Thread
    # ===================================================

    def stop(self):
        """
        Stop camera thread safely.
        """

        self.running = False

        if self.isRunning():
            self.wait(2000)

        self.release_camera()

    # ===================================================
    # Release Camera
    # ===================================================

    def release_camera(self):
        """
        Release webcam resources.
        """

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

            self.cap = None

        self.camera_status.emit(False)