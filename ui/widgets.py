from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QProgressBar
)
from PyQt6.QtCore import Qt

from ui.styles import *


# ==========================================
# Dashboard Card
# ==========================================

class CardWidget(QFrame):

    def __init__(self, title="", value="", parent=None):
        super().__init__(parent)

        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.title = QLabel(title)
        self.title.setStyleSheet(f"""
            color:{TEXT_SECONDARY};
            font-size:11pt;
        """)

        self.value = QLabel(value)
        self.value.setStyleSheet(f"""
            color:{TEXT};
            font-size:22pt;
            font-weight:bold;
        """)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)

    def setValue(self, text):
        self.value.setText(str(text))


# ==========================================
# Status Card
# ==========================================

class StatusCard(CardWidget):

    def __init__(self, title, status="Offline"):
        super().__init__(title, status)

    def setStatus(self, status, color=SUCCESS):

        self.value.setText(status)

        self.value.setStyleSheet(f"""
            color:{color};
            font-size:18pt;
            font-weight:bold;
        """)


# ==========================================
# Progress Card
# ==========================================

class ProgressCard(QFrame):

    def __init__(self, title):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15,15,15,15)

        label = QLabel(title)

        self.progress = QProgressBar()
        self.progress.setRange(0,100)

        self.value = QLabel("0 %")

        layout.addWidget(label)
        layout.addWidget(self.progress)
        layout.addWidget(self.value)

    def setValue(self,value):

        self.progress.setValue(value)
        self.value.setText(f"{value} %")


# ==========================================
# Sidebar Button
# ==========================================

class SidebarButton(QPushButton):

    def __init__(self,text):

        super().__init__(text)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumHeight(45)


# ==========================================
# Action Card
# ==========================================

class ActionCard(QFrame):

    def __init__(self,title):

        super().__init__()

        layout=QHBoxLayout(self)

        self.label=QLabel(title)

        layout.addWidget(self.label)