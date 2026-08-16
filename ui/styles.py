# ui/styles.py

# =========================
# COLORS
# =========================

BACKGROUND = "#0B1020"
CARD = "#151C2E"
CARD_HOVER = "#1B2440"

PRIMARY = "#8B5CF6"
PRIMARY_HOVER = "#9F6EFF"

SUCCESS = "#22C55E"
WARNING = "#FACC15"
DANGER = "#EF4444"

TEXT = "#FFFFFF"
TEXT_SECONDARY = "#B6BED1"

BORDER = "#2A3553"

# =========================
# RADIUS
# =========================

WINDOW_RADIUS = 18
CARD_RADIUS = 14
BUTTON_RADIUS = 10

# =========================
# SPACING
# =========================

PADDING = 15
MARGIN = 12

# =========================
# FONT
# =========================

TITLE_FONT = ("Segoe UI", 18, "bold")
SUBTITLE_FONT = ("Segoe UI", 11)
BODY_FONT = ("Segoe UI", 10)

# =========================
# ANIMATION
# =========================

ANIMATION_DURATION = 250

# =========================
# GLOBAL STYLESHEET
# =========================

GLOBAL_STYLE = f"""
QMainWindow {{
    background-color: {BACKGROUND};
}}

QWidget {{
    color: {TEXT};
    font-family: Segoe UI;
}}

QFrame {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {CARD_RADIUS}px;
}}

QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: {BUTTON_RADIUS}px;
    padding: 8px;
}}

QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
}}

QLabel {{
    color: {TEXT};
}}

QProgressBar {{
    border: none;
    border-radius: 6px;
    background: #222B42;
}}

QProgressBar::chunk {{
    background: {PRIMARY};
    border-radius: 6px;
}}
"""