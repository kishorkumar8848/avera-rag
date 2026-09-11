"""
Screen 2: Module Selection Screen for AVERA Kiosk.
Provides two prominent medical consultation tiles:
1. Speech Assistant (Microphone only)
2. Speech + Camera (Live camera inspection + voice symptoms)
"""

from typing import Callable

from app.ui.qt_compat import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, Qt, HAS_QT


class ModuleScreen(QWidget if HAS_QT else object):
    """
    Second Screen: Allows user to choose between voice consultation
    or camera + voice multimodal inspection.
    """

    def __init__(
        self,
        on_speech_selected: Callable[[], None],
        on_camera_selected: Callable[[], None],
        parent=None
    ):
        if HAS_QT:
            super().__init__(parent)
        self.on_speech_selected = on_speech_selected
        self.on_camera_selected = on_camera_selected
        if HAS_QT:
            self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(28)

        # Header Title Area
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title = QLabel("Choose Assistance Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;")
        header_layout.addWidget(title)

        subtitle = QLabel("Select whether to speak your symptoms or use the camera to inspect a visible condition")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #64748B; font-weight: 500;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_container)

        # Module Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        # Module 1: Speech Assistant
        speech_card = QFrame()
        speech_card.setObjectName("CardFrame")
        speech_layout = QVBoxLayout(speech_card)
        speech_layout.setContentsMargins(32, 32, 32, 32)
        speech_layout.setSpacing(18)

        m1_icon = QLabel("🎙️")
        m1_icon.setAlignment(Qt.AlignCenter)
        m1_icon.setStyleSheet("font-size: 52px; background: transparent;")
        speech_layout.addWidget(m1_icon)

        m1_title = QLabel("Speech Assistant")
        m1_title.setAlignment(Qt.AlignCenter)
        m1_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A; background: transparent;")
        speech_layout.addWidget(m1_title)

        m1_desc = QLabel("Speak in your preferred language to check fever, cold, cough, headache, abdominal pain, or health protocols.")
        m1_desc.setAlignment(Qt.AlignCenter)
        m1_desc.setWordWrap(True)
        m1_desc.setStyleSheet("color: #475569; font-size: 15px; line-height: 1.4; background: transparent;")
        speech_layout.addWidget(m1_desc)

        speech_layout.addStretch()

        speech_btn = QPushButton("Start Speech Assistant  ➔")
        speech_btn.setObjectName("PrimaryBtn")
        speech_btn.setMinimumHeight(60)
        speech_btn.setCursor(Qt.PointingHandCursor)
        speech_btn.clicked.connect(self.on_speech_selected)
        speech_layout.addWidget(speech_btn)

        cards_layout.addWidget(speech_card)

        # Module 2: Speech + Camera
        camera_card = QFrame()
        camera_card.setObjectName("CardFrame")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(32, 32, 32, 32)
        camera_layout.setSpacing(18)

        m2_icon = QLabel("📷")
        m2_icon.setAlignment(Qt.AlignCenter)
        m2_icon.setStyleSheet("font-size: 52px; background: transparent;")
        camera_layout.addWidget(m2_icon)

        m2_title = QLabel("Speech + Camera")
        m2_title.setAlignment(Qt.AlignCenter)
        m2_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A; background: transparent;")
        camera_layout.addWidget(m2_title)

        m2_desc = QLabel("Capture a live photo of a visible skin condition, rash, wound, burn, eye redness, or bite, then describe symptoms.")
        m2_desc.setAlignment(Qt.AlignCenter)
        m2_desc.setWordWrap(True)
        m2_desc.setStyleSheet("color: #475569; font-size: 15px; line-height: 1.4; background: transparent;")
        camera_layout.addWidget(m2_desc)

        camera_layout.addStretch()

        camera_btn = QPushButton("Open Camera + Speech  ➔")
        camera_btn.setObjectName("PrimaryBtn")
        camera_btn.setMinimumHeight(60)
        camera_btn.setCursor(Qt.PointingHandCursor)
        camera_btn.clicked.connect(self.on_camera_selected)
        camera_layout.addWidget(camera_btn)

        cards_layout.addWidget(camera_card)

        layout.addLayout(cards_layout, stretch=1)
