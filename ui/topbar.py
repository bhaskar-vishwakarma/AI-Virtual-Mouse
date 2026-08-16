from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QPushButton
)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from ui.styles import *


class TopBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(70)

        self.setup_ui()
        self.start_clock()

    def setup_ui(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # =========================
        # Title
        # =========================

        self.title = QLabel("AI Virtual Mouse V3")

        self.title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        self.title.setStyleSheet(f"""
            color:{TEXT};
        """)

        layout.addWidget(self.title)

        layout.addStretch()

        # =========================
        # Camera Status
        # =========================

        self.camera_status = QLabel("🟢 Camera Connected")

        self.camera_status.setStyleSheet(f"""
            color:{SUCCESS};
            font-size:12pt;
        """)

        layout.addWidget(self.camera_status)

        # =========================
        # Mode
        # =========================

        self.mode = QLabel("Mode : Mouse")

        self.mode.setStyleSheet(f"""
            color:{TEXT};
            font-size:12pt;
        """)

        layout.addWidget(self.mode)

        # =========================
        # FPS
        # =========================

        self.fps = QLabel("FPS : 0")

        self.fps.setStyleSheet(f"""
            color:{PRIMARY};
            font-size:12pt;
            font-weight:bold;
        """)

        layout.addWidget(self.fps)

        # =========================
        # Clock
        # =========================

        self.clock = QLabel("--:--:--")

        self.clock.setStyleSheet(f"""
            color:{TEXT_SECONDARY};
            font-size:12pt;
        """)

        layout.addWidget(self.clock)

        # =========================
        # Settings Button
        # =========================

        self.settings_btn = QPushButton("⚙")

        self.settings_btn.setFixedSize(40, 40)

        layout.addWidget(self.settings_btn)

    # ===================================
    # Live Clock
    # ===================================

    def start_clock(self):

        self.timer = QTimer(self)

        self.timer.timeout.connect(self.update_clock)

        self.timer.start(1000)

        self.update_clock()

    def update_clock(self):

        current = datetime.now().strftime("%I:%M:%S %p")

        self.clock.setText(current)

    # ===================================
    # Public Methods
    # ===================================

    def update_fps(self, fps):

        self.fps.setText(f"FPS : {fps}")

    def update_mode(self, mode):

        self.mode.setText(f"Mode : {mode}")

    def update_camera_status(self, connected=True):

        if connected:
            self.camera_status.setText("🟢 Camera Connected")
            self.camera_status.setStyleSheet(
                f"color:{SUCCESS}; font-size:12pt;"
            )
        else:
            self.camera_status.setText("🔴 Camera Disconnected")
            self.camera_status.setStyleSheet(
                f"color:{DANGER}; font-size:12pt;"
            )