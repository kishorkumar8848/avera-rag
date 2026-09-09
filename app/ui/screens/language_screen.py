"""
Screen 1: Language Selection Screen for Vyoma Kiosk.
Presents large touch targets (60-80px) for supported languages.
"""

from typing import Callable, Dict

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QScrollArea, QFrame, Qt, Signal, HAS_QT
)

from app.core.config import settings


class LanguageScreen(QWidget if HAS_QT else object):
    """
    First Screen: Allows patient or frontline healthcare worker to tap their preferred language.
    """

    def __init__(self, on_language_selected: Callable[[str], None], parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_language_selected = on_language_selected
        if HAS_QT:
            self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(20)

        # Header Title
        title_label = QLabel("Select Language / भाषा चुनें / மொழியைத் தேர்ந்தெடுக்கவும்")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00E8C6;")
        main_layout.addWidget(title_label)

        sub_label = QLabel("Tap your language to begin offline medical consultation")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet("font-size: 16px; color: #94A3B8;")
        main_layout.addWidget(sub_label)

        # Grid of Language Buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)

        languages = settings.SUPPORTED_LANGUAGES
        col_count = 2
        for idx, (lang_code, lang_name) in enumerate(languages.items()):
            row = idx // col_count
            col = idx % col_count

            btn = QPushButton(lang_name)
            btn.setObjectName("PrimaryBtn" if lang_code == "en" else "")
            btn.setMinimumHeight(68)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, code=lang_code: self.on_language_selected(code))
            grid.addWidget(btn, row, col)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)
