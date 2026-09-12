"""
Screen 1: Language Selection Screen for AVERA Kiosk.
Presents a clean, high-contrast 2-column grid of language cards with chevron navigation,
matching the official AVERA Medical UI design.
"""

from typing import Callable, Dict

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QScrollArea, QFrame, Qt, HAS_QT
)

from app.core.config import settings


# Display names and native scripts matching reference mockup
LANGUAGE_DISPLAY_MAP = [
    ("en", "English"),
    ("hi", "हिन्दी (Hindi)"),
    ("ta", "தமிழ் (Tamil)"),
    ("te", "తెలుగు (Telugu)"),
    ("kn", "ಕನ್ನಡ (Kannada)"),
    ("ml", "മലയാളം (Malayalam)"),
    ("bn", "বাংলা (Bengali)"),
    ("mr", "मराठी (Marathi)"),
    ("gu", "ગુજરાતી (Gujarati)"),
    ("pa", "ਪੰਜਾਬੀ (Punjabi)")
]


class LanguageScreen(QWidget if HAS_QT else object):
    """
    First Screen: Displays 2-column responsive grid of clean medical language cards.
    """

    def __init__(self, on_language_selected: Callable[[str], None], parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_language_selected = on_language_selected
        self.selected_code = "en"
        self.card_buttons: Dict[str, QPushButton] = {}
        if HAS_QT:
            self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(48, 32, 48, 32)
        main_layout.setSpacing(24)

        # Header Title Area
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_label = QLabel("Select Language")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;")
        header_layout.addWidget(title_label)

        sub_label = QLabel("Tap your language to begin offline medical consultation")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet("font-size: 16px; color: #64748B; font-weight: 500;")
        header_layout.addWidget(sub_label)

        main_layout.addWidget(header_container)

        # 2-Column Grid of Language Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)
        grid.setContentsMargins(12, 8, 12, 8)

        for idx, (lang_code, lang_name) in enumerate(LANGUAGE_DISPLAY_MAP):
            row = idx // 2
            col = idx % 2

            # Card Button with chevron arrow on right
            btn = QPushButton()
            btn.setObjectName("ActiveLangCard" if lang_code == "en" else "LangCard")
            btn.setMinimumHeight(64)
            btn.setCursor(Qt.PointingHandCursor)

            # Button internal layout with text on left and '>' chevron on right
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(20, 0, 20, 0)

            lbl_text = QLabel(lang_name)
            lbl_text.setStyleSheet("font-size: 18px; font-weight: 700; background: transparent;")
            if lang_code == "en":
                lbl_text.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF; background: transparent;")
            else:
                lbl_text.setStyleSheet("font-size: 18px; font-weight: 700; color: #1E293B; background: transparent;")

            chevron = QLabel("›")
            chevron.setStyleSheet("font-size: 26px; font-weight: bold; background: transparent;")
            if lang_code == "en":
                chevron.setStyleSheet("font-size: 26px; font-weight: bold; color: #FFFFFF; background: transparent;")
            else:
                chevron.setStyleSheet("font-size: 26px; font-weight: bold; color: #2563EB; background: transparent;")

            btn_layout.addWidget(lbl_text)
            btn_layout.addStretch()
            btn_layout.addWidget(chevron)

            # Store references to update active card state
            btn.lbl_text = lbl_text
            btn.chevron = chevron
            self.card_buttons[lang_code] = btn

            btn.clicked.connect(lambda checked=False, code=lang_code: self._handle_selection(code))
            grid.addWidget(btn, row, col)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, stretch=1)

        # Bottom footer tagline matching reference
        footer = QLabel("Better Care  •  Brighter Communities")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 13px; color: #94A3B8; font-weight: 600;")
        main_layout.addWidget(footer)

    def _handle_selection(self, lang_code: str):
        self.selected_code = lang_code
        # Highlight clicked card in bright blue, others in white
        for code, btn in self.card_buttons.items():
            if code == lang_code:
                btn.setObjectName("ActiveLangCard")
                btn.lbl_text.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF; background: transparent;")
                btn.chevron.setStyleSheet("font-size: 26px; font-weight: bold; color: #FFFFFF; background: transparent;")
            else:
                btn.setObjectName("LangCard")
                btn.lbl_text.setStyleSheet("font-size: 18px; font-weight: 700; color: #1E293B; background: transparent;")
                btn.chevron.setStyleSheet("font-size: 26px; font-weight: bold; color: #2563EB; background: transparent;")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if self.on_language_selected:
            self.on_language_selected(lang_code)
