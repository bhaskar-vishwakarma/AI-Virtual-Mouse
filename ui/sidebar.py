from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy
)

from PyQt6.QtCore import Qt

from ui.widgets import SidebarButton
from ui.styles import *


class Sidebar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(230)

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(12)

        # ==========================
        # Logo
        # ==========================

        logo = QLabel("🤖 AI Virtual Mouse")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo.setStyleSheet(f"""
            font-size:18px;
            font-weight:bold;
            color:{PRIMARY};
        """)

        layout.addWidget(logo)

        layout.addSpacing(20)

        # ==========================
        # Navigation Buttons
        # ==========================

        self.dashboard_btn = SidebarButton("🏠  Dashboard")
        self.gesture_btn = SidebarButton("✋  Gestures")
        self.mouse_btn = SidebarButton("🖱  Mouse")
        self.media_btn = SidebarButton("🎵  Media")
        self.analytics_btn = SidebarButton("📊  Analytics")
        self.profile_btn = SidebarButton("👤  Profiles")
        self.settings_btn = SidebarButton("⚙  Settings")
        self.help_btn = SidebarButton("❓  Help")

        buttons = [
            self.dashboard_btn,
            self.gesture_btn,
            self.mouse_btn,
            self.media_btn,
            self.analytics_btn,
            self.profile_btn,
            self.settings_btn,
            self.help_btn,
        ]

        for button in buttons:
            layout.addWidget(button)

        layout.addStretch()

        # ==========================
        # Footer
        # ==========================

        version = QLabel("Version 3.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version.setStyleSheet(f"""
            color:{TEXT_SECONDARY};
            font-size:11px;
        """)

        layout.addWidget(version)