"""
AVERA - Offline Medical AI Assistant - Main Native Touchscreen Kiosk UI.
Clean, modern, high-contrast Medical White & Royal Blue design system
optimized for touchscreen kiosks, field tablets, and desktop displays.
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
from app.safety.patient_registry import patient_registry, PatientRecord
from app.ui.styles import KIOSK_STYLESHEET
from app.ui.screens.language_screen import LanguageScreen
from app.ui.screens.module_screen import ModuleScreen
from app.ui.screens.speech_screen import SpeechScreen, CitizenSearchDialog
from app.ui.screens.camera_screen import CameraScreen


class AverKioskApp(QMainWindow if HAS_QT else object):
    """
    Main AVERA Kiosk Application Container managing responsive window layout,
    clean medical top navigation bar, screen stack, and telemetry clock.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        if HAS_QT:
            super().__init__()
        self.retriever = retriever or HybridRetriever()
        self.active_language = settings.DEFAULT_LANGUAGE
        self.active_patient: Optional[PatientRecord] = patient_registry.get_patient("P001")  # Default to Kishor Kumar

        if HAS_QT:
            self._init_window()
            self._init_topbar()
            self._init_screens()
            self._init_clock_and_telemetry()

    def _init_window(self):
        self.setWindowTitle("AVERA - Medical AI Assistant (ASHA Village Health Kiosk)")
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
        bar_layout.setContentsMargins(20, 0, 20, 0)
        bar_layout.setSpacing(16)

        # Navigation Buttons (Left-most)
        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setObjectName("NavBtn")
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.clicked.connect(self.navigate_home)
        bar_layout.addWidget(self.home_btn)

        self.back_btn = QPushButton("⬅️ Back")
        self.back_btn.setObjectName("NavBtn")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.navigate_back)
        bar_layout.addWidget(self.back_btn)

        # Medical Cross Icon
        cross_icon = QLabel("✚")
        cross_icon.setStyleSheet("font-size: 28px; font-weight: 900; color: #2563EB; background: transparent;")
        bar_layout.addWidget(cross_icon)

        # Left Branding Block: AVERA + Medical AI Assistant
        brand_box = QWidget()
        brand_box.setStyleSheet("background: transparent;")
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(0, 8, 0, 8)
        brand_layout.setSpacing(0)

        self.title_lbl = QLabel("AVERA")
        self.title_lbl.setObjectName("TopBarBrand")
        brand_layout.addWidget(self.title_lbl)

        self.subtitle_lbl = QLabel("Medical AI Assistant")
        self.subtitle_lbl.setObjectName("TopBarTagline")
        brand_layout.addWidget(self.subtitle_lbl)

        bar_layout.addWidget(brand_box)

        # Vertical Divider Line
        divider = QFrame()
        divider.setObjectName("TopBarDivider")
        bar_layout.addWidget(divider)

        # Kiosk Village Subheader
        sub_box = QWidget()
        sub_box.setStyleSheet("background: transparent;")
        sub_layout = QVBoxLayout(sub_box)
        sub_layout.setContentsMargins(0, 8, 0, 8)
        sub_layout.setSpacing(1)

        kiosk_title = QLabel("ASHA Village Health Kiosk")
        kiosk_title.setObjectName("TopBarSubHeader")
        sub_layout.addWidget(kiosk_title)

        kiosk_motto = QLabel("Accessible Healthcare for a Healthier Tomorrow")
        kiosk_motto.setObjectName("TopBarMotto")
        sub_layout.addWidget(kiosk_motto)

        bar_layout.addWidget(sub_box)

        bar_layout.addStretch()

        # Right Block: Live Clock
        self.clock_lbl = QLabel()
        self.clock_lbl.setObjectName("TopBarClock")
        self._update_clock()
        bar_layout.addWidget(self.clock_lbl)

        # Active Citizen Button / Badge (Clickable to switch citizen)
        self.patient_btn = QPushButton()
        self.patient_btn.setObjectName("PatientBadgeBtn")
        self.patient_btn.setCursor(Qt.PointingHandCursor)
        self.patient_btn.clicked.connect(self._open_citizen_dialog)
        self._refresh_patient_display()
        bar_layout.addWidget(self.patient_btn)

        # Language Badge
        self.lang_badge = QLabel("Lang: EN")
        self.lang_badge.setObjectName("TopBarTelemetry")
        bar_layout.addWidget(self.lang_badge)

        # Fullscreen Toggle Button
        self.fs_btn = QPushButton("⛶ Fullscreen")
        self.fs_btn.setObjectName("NavBtn")
        self.fs_btn.setCursor(Qt.PointingHandCursor)
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        bar_layout.addWidget(self.fs_btn)

        # Hardware Telemetry Badge (RAM & CPU)
        self.telemetry_lbl = QLabel("RAM: -- | CPU: --")
        self.telemetry_lbl.setObjectName("TopBarTelemetry")
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
        self.screen_speech.on_patient_changed = self._on_screen_patient_changed
        if hasattr(self.screen_speech, "set_patient") and self.active_patient:
            self.screen_speech.set_patient(self.active_patient)
        self.stack.addWidget(self.screen_speech)

        # Screen 3: Camera + Speech Screen
        self.screen_camera = CameraScreen(retriever=self.retriever)
        if hasattr(self.screen_camera, "set_patient") and self.active_patient:
            self.screen_camera.set_patient(self.active_patient)
        self.stack.addWidget(self.screen_camera)

        self.main_layout.addWidget(self.stack, stretch=1)
        self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def _init_clock_and_telemetry(self):
        # Digital Clock Timer (Every 15s)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(15000)

        # Hardware Monitor Telemetry (Every 3s)
        monitor.start()
        self.telem_timer = QTimer(self)
        self.telem_timer.timeout.connect(self._update_telemetry)
        self.telem_timer.start(3000)

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now()
        # Formatted e.g. "Sep 11, 2026  09:02 AM"
        self.clock_lbl.setText(now.strftime("%b %d, %Y  %I:%M %p"))

    def _update_telemetry(self):
        stats = monitor.get_stats()
        ram_pct = stats.get("ram_percent", 0.0)
        cpu_pct = stats.get("cpu_percent", 0.0)
        temp_c = stats.get("temperature_c")
        temp_str = f" | {temp_c}°C" if temp_c else ""
        self.telemetry_lbl.setText(f"RAM: {ram_pct:.0f}% | CPU: {cpu_pct:.0f}%{temp_str}")

    def _open_citizen_dialog(self):
        dialog = CitizenSearchDialog(parent=self, on_selected=self._set_active_patient)
        dialog.exec()

    def _set_active_patient(self, patient: PatientRecord):
        self.active_patient = patient
        self._refresh_patient_display()
        if hasattr(self, "screen_speech"):
            self.screen_speech.set_patient(patient)
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "set_patient"):
            self.screen_camera.set_patient(patient)

    def _on_screen_patient_changed(self, summary_text: str):
        self.patient_btn.setText(f"👤 {summary_text}")

    def _refresh_patient_display(self):
        if self.active_patient:
            badge = f"👤 {self.active_patient.name} ({self.active_patient.age_display_badge})"
        else:
            badge = "👤 Select Citizen"
        self.patient_btn.setText(badge)

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
        # If camera screen has viewfinder starter, trigger it
        if hasattr(self.screen_camera, "start_viewfinder"):
            self.screen_camera.start_viewfinder()

    def navigate_home(self):
        self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def navigate_back(self):
        curr = self.stack.currentIndex()
        if curr in [2, 3]:
            # Stop viewfinder if leaving camera
            if curr == 3 and hasattr(self.screen_camera, "stop_viewfinder"):
                self.screen_camera.stop_viewfinder()
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

    def closeEvent(self, event):
        monitor.stop()
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "stop_viewfinder"):
            self.screen_camera.stop_viewfinder()
        event.accept()


# Backward compatibility alias
VyomaKioskApp = AverKioskApp


def run_ui():
    """Main application entrypoint."""
    if not HAS_QT:
        print("Neither PySide6, PyQt6, nor PyQt5 is installed. Native UI requires a Qt binding.")
        return

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    window = AverKioskApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_ui()
