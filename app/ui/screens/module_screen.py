"""
Screen 2: Module Selection Screen for Vyoma Kiosk.
Provides two prominent touch tiles:
1. Speech Assistant (Microphone only)
2. Speech + Camera (Camera frame inspection + speech)
"""

from typing import Callable

from app.ui.qt_compat import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, Qt, HAS_QT


class ModuleScreen(QWidget if HAS_QT else object):
    """
    Second Screen: Lets the user select between voice-only consultation
    or camera + voice multimodal clinical guidance.
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
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)

        # Header Title
        title = QLabel("Choose Assistance Mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00E8C6;")
        layout.addWidget(title)

        subtitle = QLabel("Select whether to speak your symptoms or use the camera to inspect a visible condition")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #94A3B8;")
        layout.addWidget(subtitle)

        # Module Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        # Module 1: Speech Assistant
        speech_card = QFrame()
        speech_card.setObjectName("CardFrame")
        speech_card_layout = QVBoxLayout(speech_card)
        speech_card_layout.setContentsMargins(24, 24, 24, 24)
        speech_card_layout.setSpacing(16)

        m1_icon = QLabel("🎤")
        m1_icon.setAlignment(Qt.AlignCenter)
        m1_icon.setStyleSheet("font-size: 44px;")
        speech_card_layout.addWidget(m1_icon)

        m1_title = QLabel("Speech Assistant")
        m1_title.setAlignment(Qt.AlignCenter)
        m1_title.setObjectName("CardHeader")
        speech_card_layout.addWidget(m1_title)

        m1_desc = QLabel("Speak in your preferred language to check fever, headache, pain, or health protocols.")
        m1_desc.setAlignment(Qt.AlignCenter)
        m1_desc.setWordWrap(True)
        m1_desc.setStyleSheet("color: #CBD5E1; font-size: 15px;")
        speech_card_layout.addWidget(m1_desc)

        speech_btn = QPushButton("Start Speech Assistant")
        speech_btn.setObjectName("PrimaryBtn")
        speech_btn.setMinimumHeight(64)
        speech_btn.setCursor(Qt.PointingHandCursor)
        speech_btn.clicked.connect(self.on_speech_selected)
        speech_card_layout.addWidget(speech_btn)

        cards_layout.addWidget(speech_card)

        # Module 2: Speech + Camera
        camera_card = QFrame()
        camera_card.setObjectName("CardFrame")
        camera_card_layout = QVBoxLayout(camera_card)
        camera_card_layout.setContentsMargins(24, 24, 24, 24)
        camera_card_layout.setSpacing(16)

        m2_icon = QLabel("📷")
        m2_icon.setAlignment(Qt.AlignCenter)
        m2_icon.setStyleSheet("font-size: 44px;")
        camera_card_layout.addWidget(m2_icon)

        m2_title = QLabel("Speech + Camera")
        m2_title.setAlignment(Qt.AlignCenter)
        m2_title.setObjectName("CardHeader")
        camera_card_layout.addWidget(m2_title)

        m2_desc = QLabel("Capture a photo of a visible skin condition, bite, or sore, then speak your symptoms.")
        m2_desc.setAlignment(Qt.AlignCenter)
        m2_desc.setWordWrap(True)
        m2_desc.setStyleSheet("color: #CBD5E1; font-size: 15px;")
        camera_card_layout.addWidget(m2_desc)

        camera_btn = QPushButton("Open Camera + Speech")
        camera_btn.setMinimumHeight(64)
        camera_btn.setCursor(Qt.PointingHandCursor)
        camera_btn.clicked.connect(self.on_camera_selected)
        camera_card_layout.addWidget(camera_btn)

        cards_layout.addWidget(camera_card)

        layout.addLayout(cards_layout)
