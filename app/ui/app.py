"""
Vyoma Offline Medical AI Assistant - Main Native Touchscreen Kiosk UI.
Built on PySide6 / Qt6 for 1024x600 Waveshare Touchscreen on NVIDIA Jetson Orin Nano.
"""

import sys
import os
from typing import Optional

from app.ui.qt_compat import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, Qt, QTimer, HAS_QT
)

from app.core.config import settings
from app.core.logging import logger
from app.hardware.monitor import monitor
from app.rag.hybrid_retriever import HybridRetriever
from app.ui.styles import KIOSK_STYLESHEET
from app.ui.screens.language_screen import LanguageScreen
from app.ui.screens.module_screen import ModuleScreen
from app.ui.screens.speech_screen import SpeechScreen
from app.ui.screens.camera_screen import CameraScreen


class VyomaKioskApp(QMainWindow if HAS_QT else object):
    """
    Main Kiosk Container managing 1024x600 window layout,
    persistent top navigation bar, screen stack, and live telemetry updates.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        if HAS_QT:
            super().__init__()
        self.retriever = retriever or HybridRetriever()
        self.active_language = settings.DEFAULT_LANGUAGE

        if HAS_QT:
            self._init_window()
            self._init_topbar()
            self._init_screens()
            self._init_telemetry_timer()

    def _init_window(self):
        self.setWindowTitle("Vyoma Offline Medical AI Assistant - ASHA Village Health Kiosk")
        self.setMinimumSize(960, 560)
        self.resize(settings.UI_WIDTH, settings.UI_HEIGHT)
        self.setStyleSheet(KIOSK_STYLESHEET)

        # Central container
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.central_widget)

        if settings.FULLSCREEN:
            self.showFullScreen()
        else:
            self.showMaximized()

    def _init_topbar(self):
        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        bar_layout = QHBoxLayout(self.top_bar)
        bar_layout.setContentsMargins(16, 0, 16, 0)
        bar_layout.setSpacing(12)

        # Home Button
        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setObjectName("NavBtn")
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.clicked.connect(self.navigate_home)
        bar_layout.addWidget(self.home_btn)

        # Back Button
        self.back_btn = QPushButton("⬅️ Back")
        self.back_btn.setObjectName("NavBtn")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.navigate_back)
        bar_layout.addWidget(self.back_btn)

        # Title
        self.title_lbl = QLabel("Vyoma ASHA Medical AI")
        self.title_lbl.setObjectName("TopBarTitle")
        bar_layout.addWidget(self.title_lbl)

        bar_layout.addStretch()

        # Active Citizen Badge
        self.patient_badge = QLabel("👤 Patient: Not Selected")
        self.patient_badge.setObjectName("TopBarStatus")
        self.patient_badge.setStyleSheet("color: #38BDF8; font-weight: 600; background: #0F172A; padding: 4px 10px; border-radius: 6px;")
        bar_layout.addWidget(self.patient_badge)

        # Language Badge
        self.lang_badge = QLabel("Lang: EN")
        self.lang_badge.setObjectName("TopBarStatus")
        bar_layout.addWidget(self.lang_badge)

        # Fullscreen Toggle Button
        self.fs_btn = QPushButton("⛶ Fullscreen")
        self.fs_btn.setObjectName("NavBtn")
        self.fs_btn.setCursor(Qt.PointingHandCursor)
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        bar_layout.addWidget(self.fs_btn)

        # Hardware Telemetry Badge (RAM & CPU)
        self.telemetry_lbl = QLabel("RAM: -- | CPU: --")
        self.telemetry_lbl.setObjectName("TopBarStatus")
        bar_layout.addWidget(self.telemetry_lbl)

        self.main_layout.addWidget(self.top_bar)


    def _init_screens(self):
        self.stack = QStackedWidget()

        # Screen 0: Language Selection
        self.screen_lang = LanguageScreen(on_language_selected=self.on_language_selected)
        self.stack.addWidget(self.screen_lang)

        # Screen 1: Module Selection
        self.screen_module = ModuleScreen(
            on_speech_selected=self.open_speech_module,
            on_camera_selected=self.open_camera_module
        )
        self.stack.addWidget(self.screen_module)

        # Screen 2: Speech Assistant Screen
        self.screen_speech = SpeechScreen(retriever=self.retriever)
        self.screen_speech.on_patient_changed = self.update_active_patient_display
        if getattr(self.screen_speech, "active_patient", None):
            p = self.screen_speech.active_patient
            self.update_active_patient_display(f"{p.name} ({p.age_display_badge})")
        self.stack.addWidget(self.screen_speech)


        # Screen 3: Camera + Speech Screen
        self.screen_camera = CameraScreen(retriever=self.retriever)
        self.stack.addWidget(self.screen_camera)

        self.main_layout.addWidget(self.stack, stretch=1)
        self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def _init_telemetry_timer(self):
        monitor.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_telemetry)
        self.timer.start(2000)

    def _update_telemetry(self):
        stats = monitor.get_stats()
        ram_pct = stats.get("ram_percent", 0.0)
        cpu_pct = stats.get("cpu_percent", 0.0)
        temp_c = stats.get("temperature_c")
        temp_str = f" | {temp_c}°C" if temp_c else ""
        self.telemetry_lbl.setText(f"RAM: {ram_pct:.0f}% | CPU: {cpu_pct:.0f}%{temp_str}")

    def on_language_selected(self, lang_code: str):
        self.active_language = lang_code
        self.lang_badge.setText(f"Lang: {lang_code.upper()}")
        self.screen_speech.set_language(lang_code)
        self.screen_camera.set_language(lang_code)
        self.stack.setCurrentIndex(1)
        self.update_nav_buttons()

    def open_speech_module(self):
        self.stack.setCurrentIndex(2)
        self.update_nav_buttons()

    def open_camera_module(self):
        self.stack.setCurrentIndex(3)
        self.update_nav_buttons()

    def navigate_home(self):
        self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def navigate_back(self):
        curr = self.stack.currentIndex()
        if curr in [2, 3]:
            self.stack.setCurrentIndex(1)
        elif curr == 1:
            self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        curr = self.stack.currentIndex()
        self.home_btn.setEnabled(curr != 0)
        self.back_btn.setEnabled(curr != 0)

    def toggle_fullscreen(self):

        """Toggles between Fullscreen and Maximized Window."""
        if self.isFullScreen():
            self.showMaximized()
            self.fs_btn.setText("⛶ Fullscreen")
        else:
            self.showFullScreen()
            self.fs_btn.setText("🗗 Windowed")

    def keyPressEvent(self, event):
        """Hotkeys: F11 for Fullscreen toggle, Esc to exit Fullscreen."""
        key = event.key()
        f11_key = getattr(Qt, "Key_F11", 0x0100003a)
        esc_key = getattr(Qt, "Key_Escape", 0x01000000)
        if key == f11_key:
            self.toggle_fullscreen()
        elif key == esc_key and self.isFullScreen():
            self.showMaximized()
            self.fs_btn.setText("⛶ Fullscreen")
        else:
            super().keyPressEvent(event)

    def update_active_patient_display(self, patient_summary: str):
        """Updates persistent top-bar badge with active citizen."""
        self.patient_badge.setText(f"👤 {patient_summary}")

    def closeEvent(self, event):
        monitor.stop()
        event.accept()



def run_ui():
    """Main application entrypoint."""
    if not HAS_QT:
        print("Neither PySide6 nor PyQt6 is installed. Native UI requires PySide6 or PyQt6.")
        return

    # High-DPI and Touchscreen scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    window = VyomaKioskApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_ui()
