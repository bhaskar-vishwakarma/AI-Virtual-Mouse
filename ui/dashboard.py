from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame
)

from PyQt6.QtCore import Qt

from ui.widgets import (
    CardWidget,
    ProgressCard,
    StatusCard,
)

from ui.styles import *


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setup_ui()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(15)

        # ===================================================
        # CAMERA + VIRTUAL DESKTOP
        # ===================================================

        top_layout = QHBoxLayout()

        # Camera Feed
        self.camera_frame = QFrame()

        camera_layout = QVBoxLayout(self.camera_frame)

        camera_title = QLabel("📷 Live Camera Feed")
        camera_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.camera_label = QLabel("Camera Preview")

        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(640,360)

        camera_layout.addWidget(camera_title)
        camera_layout.addWidget(self.camera_label)

        # Virtual Desktop

        self.desktop_frame = QFrame()

        desktop_layout = QVBoxLayout(self.desktop_frame)

        desktop_title = QLabel("🖥 Virtual Desktop")
        desktop_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.desktop_preview = QLabel("Desktop Preview")

        self.desktop_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desktop_preview.setMinimumSize(320,360)

        desktop_layout.addWidget(desktop_title)
        desktop_layout.addWidget(self.desktop_preview)

        top_layout.addWidget(self.camera_frame,2)
        top_layout.addWidget(self.desktop_frame,1)

        main_layout.addLayout(top_layout)

        # ===================================================
        # INFO CARDS
        # ===================================================

        grid = QGridLayout()

        self.gesture_card = CardWidget("Gesture","None")

        self.confidence_card = CardWidget("Confidence","0 %")

        self.cursor_card = CardWidget("Cursor","(0,0)")

        self.fps_card = CardWidget("FPS","0")

        self.volume_card = ProgressCard("Volume")

        self.brightness_card = ProgressCard("Brightness")

        self.status_card = StatusCard("System","Ready")

        self.action_card = CardWidget("Recent Action","Waiting...")

        grid.addWidget(self.gesture_card,0,0)
        grid.addWidget(self.confidence_card,0,1)
        grid.addWidget(self.cursor_card,0,2)
        grid.addWidget(self.fps_card,0,3)

        grid.addWidget(self.volume_card,1,0)
        grid.addWidget(self.brightness_card,1,1)
        grid.addWidget(self.status_card,1,2)
        grid.addWidget(self.action_card,1,3)

        main_layout.addLayout(grid)