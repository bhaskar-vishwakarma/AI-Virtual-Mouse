from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QKeySequence, QShortcut

from ui.sidebar import Sidebar
from ui.topbar import TopBar
from ui.dashboard import Dashboard
from ui.styles import GLOBAL_STYLE, SUCCESS, WARNING, DANGER

from core.camera_thread import CameraThread
from core.input_pipeline import InputPipeline


class MainWindow(QMainWindow):

    # Windows volume keys move the level in 2% steps. The bar is an
    # estimate only -- nothing here reads the real system volume.
    VOLUME_STEP_PERCENT = 2

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Virtual Mouse V3")
        self.resize(1600, 900)

        self.setStyleSheet(GLOBAL_STYLE)

        self.camera_thread = None
        self.pipeline = None

        # Gesture control starts paused so the application can
        # never grab input before the user asks for it.
        self.control_active = False

        self.volume_estimate = 50

        self.build_ui()
        self.setup_pipeline()
        self.setup_camera()
        self.setup_shortcuts()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.topbar = TopBar()
        self.dashboard = Dashboard()

        right_layout.addWidget(self.topbar)
        right_layout.addWidget(self.dashboard)

        main_layout.addWidget(right_container)

        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 5)

        # ------------------------------------------------------
        # Control toggle
        # ------------------------------------------------------

        self.sidebar.mouse_btn.setText(
            "▶  Start Control"
        )

        self.sidebar.mouse_btn.clicked.connect(
            self.toggle_control
        )

        self.dashboard.status_card.setStatus(
            "Paused",
            WARNING,
        )

        self.topbar.update_mode(
            "Paused"
        )

    # ==========================================================
    # SHORTCUTS
    # ==========================================================

    def setup_shortcuts(self):
        """
        Esc is a panic switch that always pauses gesture control.
        """

        self.stop_shortcut = QShortcut(
            QKeySequence("Esc"),
            self,
        )

        self.stop_shortcut.activated.connect(
            self.stop_control
        )

    # ==========================================================
    # PIPELINE
    # ==========================================================

    def setup_pipeline(self):

        try:

            self.pipeline = InputPipeline()

            # Built disabled; toggle_control turns it on.
            self.pipeline.disable()

        except Exception as e:

            self.pipeline = None

            print(
                f"[MainWindow] Pipeline unavailable: {e}"
            )

            self.dashboard.status_card.setStatus(
                "Pipeline error",
                DANGER,
            )

    def toggle_control(self):

        if self.pipeline is None:
            return

        if self.control_active:

            self.stop_control()

        else:

            self.start_control()

    def start_control(self):

        if self.pipeline is None:
            return

        self.pipeline.enable()

        self.control_active = True

        self.sidebar.mouse_btn.setText(
            "⏸  Stop Control"
        )

        self.dashboard.status_card.setStatus(
            "Active",
            SUCCESS,
        )

        self.topbar.update_mode(
            "Active"
        )

    def stop_control(self):

        if self.pipeline is None:
            return

        self.pipeline.disable()

        self.control_active = False

        self.sidebar.mouse_btn.setText(
            "▶  Start Control"
        )

        self.dashboard.status_card.setStatus(
            "Paused",
            WARNING,
        )

        self.topbar.update_mode(
            "Paused"
        )

    # ==========================================================
    # CAMERA
    # ==========================================================

    def setup_camera(self):

        self.camera_thread = CameraThread(
            camera_index=0,
            width=1280,
            height=720,
            parent=self,
        )

        self.camera_thread.frame_ready.connect(
            self.update_camera_frame
        )

        self.camera_thread.fps_updated.connect(
            self.update_fps
        )

        self.camera_thread.camera_status.connect(
            self.update_camera_status
        )

        self.camera_thread.start()

    # ==========================================================
    # FRAME HANDLING
    # ==========================================================

    def update_camera_frame(self, frame):

        if frame is None:
            return

        display_frame = frame

        # ------------------------------------------------------
        # Run the gesture pipeline
        # ------------------------------------------------------

        if (
            self.pipeline is not None
            and self.control_active
        ):

            try:

                result = self.pipeline.process(
                    frame
                )

                processed = result.get(
                    "frame"
                )

                if processed is not None:

                    display_frame = processed

                self.update_dashboard(
                    result
                )

            except Exception as e:

                print(
                    f"[MainWindow] Pipeline error: {e}"
                )

        self.render_frame(
            display_frame
        )

    def render_frame(self, frame):

        try:

            rgb_frame = frame[:, :, ::-1].copy()

            height, width, channels = rgb_frame.shape
            bytes_per_line = channels * width

            image = QImage(
                rgb_frame.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )

            pixmap = QPixmap.fromImage(image)

            label_size = self.dashboard.camera_label.size()

            if label_size.width() <= 0 or label_size.height() <= 0:
                return

            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            self.dashboard.camera_label.setPixmap(
                scaled_pixmap
            )

        except Exception as e:

            print(
                f"[MainWindow] Camera display error: {e}"
            )

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    def update_dashboard(self, result):

        if not result:
            return

        try:

            # --------------------------------------------------
            # Gesture
            # --------------------------------------------------

            self.dashboard.gesture_card.setValue(
                result.get(
                    "gesture",
                    "NONE",
                )
            )

            # --------------------------------------------------
            # Confidence
            # --------------------------------------------------

            confidence = float(
                result.get(
                    "confidence",
                    0.0,
                )
            )

            self.dashboard.confidence_card.setValue(
                f"{confidence * 100:.0f} %"
            )

            # --------------------------------------------------
            # Cursor
            # --------------------------------------------------

            cursor = result.get(
                "cursor"
            )

            if cursor is not None:

                self.dashboard.cursor_card.setValue(
                    f"({cursor[0]}, {cursor[1]})"
                )

            # --------------------------------------------------
            # Recent action
            # --------------------------------------------------

            action = result.get(
                "action"
            )

            if action:

                self.dashboard.action_card.setValue(
                    action
                )

                self.update_volume_estimate(
                    action
                )

        except Exception as e:

            print(
                f"[MainWindow] Dashboard update error: {e}"
            )

    def update_volume_estimate(self, action):
        """
        Track an approximate volume level from the events we sent.

        This is an estimate, not a reading of the real mixer, and
        it drifts if the user changes volume by other means.
        """

        if action == "VOLUME_UP":

            self.volume_estimate = min(
                100,
                self.volume_estimate
                + self.VOLUME_STEP_PERCENT,
            )

        elif action == "VOLUME_DOWN":

            self.volume_estimate = max(
                0,
                self.volume_estimate
                - self.VOLUME_STEP_PERCENT,
            )

        elif action == "MUTE":

            self.volume_estimate = 0

        else:
            return

        self.dashboard.volume_card.setValue(
            self.volume_estimate
        )

    # ==========================================================
    # FPS
    # ==========================================================

    def update_fps(self, fps):

        try:

            self.dashboard.fps_card.setValue(
                f"{fps:.1f}"
            )

            self.topbar.update_fps(
                f"{fps:.1f}"
            )

        except Exception:
            pass

    # ==========================================================
    # CAMERA STATUS
    # ==========================================================

    def update_camera_status(self, connected):

        self.topbar.update_camera_status(
            connected
        )

        if connected:

            self.dashboard.camera_label.clear()

            return

        self.stop_control()

        self.dashboard.camera_label.clear()

        self.dashboard.camera_label.setText(
            "Camera unavailable"
        )

        self.dashboard.status_card.setStatus(
            "Camera lost",
            DANGER,
        )

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def closeEvent(self, event):

        if self.camera_thread is not None:

            self.camera_thread.stop()
            self.camera_thread = None

        if self.pipeline is not None:

            try:

                self.pipeline.close()

            except Exception as e:

                print(
                    f"[MainWindow] Pipeline close error: {e}"
                )

            self.pipeline = None

        event.accept()
