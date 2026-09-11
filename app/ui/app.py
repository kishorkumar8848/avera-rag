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
from app.ui.screens.citizen_screen import CitizenScreen
from app.ui.screens.vitals_screen import VitalsScreen
from app.ui.screens.module_screen import ModuleScreen
from app.ui.screens.speech_screen import SpeechScreen, CitizenSearchDialog
from app.ui.screens.camera_screen import CameraScreen
from app.hardware.sensor_manager import VitalsRecord


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
        self.active_vitals: Optional[VitalsRecord] = None

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

        self.new_assess_btn = QPushButton("🔄 New")
        self.new_assess_btn.setObjectName("NavBtn")
        self.new_assess_btn.setCursor(Qt.PointingHandCursor)
        self.new_assess_btn.clicked.connect(self.start_fresh_assessment)
        bar_layout.addWidget(self.new_assess_btn)

        # Medical Cross Icon + Brand
        cross_icon = QLabel("✚")
        cross_icon.setStyleSheet("font-size: 24px; font-weight: 900; color: #2563EB; background: transparent;")
        bar_layout.addWidget(cross_icon)

        self.title_lbl = QLabel("AVERA")
        self.title_lbl.setObjectName("TopBarBrand")
        bar_layout.addWidget(self.title_lbl)

        self.subtitle_lbl = QLabel("AI")
        self.subtitle_lbl.setObjectName("TopBarTagline")
        bar_layout.addWidget(self.subtitle_lbl)

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
        self.lang_badge = QLabel("EN")
        self.lang_badge.setObjectName("TopBarTelemetry")
        bar_layout.addWidget(self.lang_badge)

        # Fullscreen Toggle Button
        self.fs_btn = QPushButton("⛶")
        self.fs_btn.setObjectName("NavBtn")
        self.fs_btn.setCursor(Qt.PointingHandCursor)
        self.fs_btn.setToolTip("Toggle Fullscreen")
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        bar_layout.addWidget(self.fs_btn)

        # Hardware Telemetry Badge (RAM)
        self.telemetry_lbl = QLabel("RAM: --")
        self.telemetry_lbl.setObjectName("TopBarTelemetry")
        bar_layout.addWidget(self.telemetry_lbl)

        self.main_layout.addWidget(self.top_bar)

    def _init_screens(self):
        self.stack = QStackedWidget()

        # Screen 0: Language Selection
        self.screen_lang = LanguageScreen(on_language_selected=self.on_language_selected)
        self.stack.addWidget(self.screen_lang)

        # Screen 1: Citizen / Resident Selection Screen
        self.screen_citizen = CitizenScreen(on_citizen_selected=self.on_citizen_selected)
        self.stack.addWidget(self.screen_citizen)

        # Screen 2: Biometric Vitals Acquisition Screen
        self.screen_vitals = VitalsScreen(on_vitals_confirmed=self.on_vitals_confirmed)
        if self.active_patient and hasattr(self.screen_vitals, "set_patient"):
            self.screen_vitals.set_patient(self.active_patient)
        self.stack.addWidget(self.screen_vitals)

        # Screen 3: Module Selection (Speech vs. Camera)
        self.screen_module = ModuleScreen(
            on_speech_selected=self.open_speech_module,
            on_camera_selected=self.open_camera_module
        )
        self.stack.addWidget(self.screen_module)

        # Screen 4: Speech Assistant Screen
        self.screen_speech = SpeechScreen(retriever=self.retriever)
        self.screen_speech.on_patient_changed = self._on_screen_patient_changed
        self.screen_speech.on_new_assessment = self.start_fresh_assessment
        if hasattr(self.screen_speech, "set_patient") and self.active_patient:
            self.screen_speech.set_patient(self.active_patient)
        self.stack.addWidget(self.screen_speech)

        # Screen 5: Camera + Speech Screen
        self.screen_camera = CameraScreen(retriever=self.retriever)
        self.screen_camera.on_new_assessment = self.start_fresh_assessment
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
        # Formatted e.g. "Sep 11, 15:30"
        self.clock_lbl.setText(now.strftime("%b %d, %H:%M"))

    def _update_telemetry(self):
        stats = monitor.get_stats()
        ram_pct = stats.get("ram_percent", 0.0)
        temp_c = stats.get("temperature_c")
        temp_str = f" {temp_c:.0f}°C" if temp_c else ""
        self.telemetry_lbl.setText(f"RAM {ram_pct:.0f}%{temp_str}")

    def _open_citizen_dialog(self):
        dialog = CitizenSearchDialog(parent=self, on_selected=self._set_active_patient)
        dialog.exec()

    def _set_active_patient(self, patient: PatientRecord):
        self.active_patient = patient
        self._refresh_patient_display()
        if hasattr(self, "screen_vitals") and hasattr(self.screen_vitals, "set_patient"):
            self.screen_vitals.set_patient(patient)
        if hasattr(self, "screen_speech"):
            self.screen_speech.set_patient(patient)
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "set_patient"):
            self.screen_camera.set_patient(patient)

    def _on_screen_patient_changed(self, summary_text: str):
        short = summary_text.split("(")[0].strip() if "(" in summary_text else summary_text
        self.patient_btn.setText(f"👤 {short}")

    def _refresh_patient_display(self):
        if self.active_patient:
            name_parts = self.active_patient.name.split()
            short_name = name_parts[0] if name_parts else "Citizen"
            badge = f"👤 {short_name} ({self.active_patient.age_display_badge})"
        else:
            badge = "👤 Citizen"
        self.patient_btn.setText(badge)

    def on_language_selected(self, lang_code: str):
        self.active_language = lang_code
        self.lang_badge.setText(f"Lang: {lang_code.upper()}")
        self.screen_speech.set_language(lang_code)
        self.screen_camera.set_language(lang_code)
        # Step 2 in kiosk flow: Citizen Selection
        self.stack.setCurrentIndex(1)
        self.update_nav_buttons()

    def on_citizen_selected(self, patient: PatientRecord):
        self._set_active_patient(patient)
        # Step 3 in kiosk flow: Biometric Vitals Acquisition
        self.stack.setCurrentIndex(2)
        self.update_nav_buttons()

    def on_vitals_confirmed(self, vitals: VitalsRecord):
        self.active_vitals = vitals
        if hasattr(self, "screen_speech") and hasattr(self.screen_speech, "set_vitals"):
            self.screen_speech.set_vitals(vitals)
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "set_vitals"):
            self.screen_camera.set_vitals(vitals)
        # Step 4 in kiosk flow: Module Selection (Speech or Camera)
        self.stack.setCurrentIndex(3)
        self.update_nav_buttons()

    def open_speech_module(self):
        # Step 5a in kiosk flow: Speech Consultation
        self.stack.setCurrentIndex(4)
        self.update_nav_buttons()

    def open_camera_module(self):
        # Step 5b in kiosk flow: Camera Multimodal Examination
        self.stack.setCurrentIndex(5)
        self.update_nav_buttons()
        if hasattr(self.screen_camera, "start_viewfinder"):
            self.screen_camera.start_viewfinder()

    def start_fresh_assessment(self):
        """
        Resets the entire kiosk state (audio, camera, vitals, patient, screen widgets)
        and redirects back to the Home page (Screen 0) for a completely fresh consultation.
        """
        try:
            from app.models.bhashini_tts import tts_service
            tts_service.stop_speaking()
        except Exception:
            pass

        # 1. Stop camera viewfinder
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "stop_viewfinder"):
            self.screen_camera.stop_viewfinder()

        # 2. Reset SpeechScreen widgets
        if hasattr(self, "screen_speech") and hasattr(self.screen_speech, "_reset_screen_state"):
            self.screen_speech._reset_screen_state()

        # 3. Reset CameraScreen widgets
        if hasattr(self, "screen_camera") and hasattr(self.screen_camera, "_reset_screen_state"):
            self.screen_camera._reset_screen_state()

        # 4. Reset VitalsScreen & SensorManager
        try:
            from app.hardware.sensor_manager import sensor_manager
            sensor_manager.reset_readings()
        except Exception:
            pass
        self.active_vitals = None
        if hasattr(self, "screen_vitals") and hasattr(self.screen_vitals, "_reset_all"):
            self.screen_vitals._reset_all()

        # 5. Reset CitizenScreen
        if hasattr(self, "screen_citizen") and hasattr(self.screen_citizen, "reset_selection"):
            self.screen_citizen.reset_selection()

        # 6. Reset active patient to default
        default_list = patient_registry.search("kishor")
        self.active_patient = default_list[0] if default_list else None
        self._refresh_patient_display()

        # 7. Redirect to Home (Screen 0: Language Selection)
        self.stack.setCurrentIndex(0)
        self.update_nav_buttons()
        logger.info("AVERA Kiosk reset completely fresh for new citizen assessment.")

    def navigate_home(self):
        """Redirects to Home page with a completely fresh state."""
        self.start_fresh_assessment()

    def navigate_back(self):
        curr = self.stack.currentIndex()
        if curr == 5:
            # Leaving camera screen -> back to module selection
            if hasattr(self.screen_camera, "stop_viewfinder"):
                self.screen_camera.stop_viewfinder()
            self.stack.setCurrentIndex(3)
        elif curr == 4:
            # Leaving speech screen -> back to module selection
            self.stack.setCurrentIndex(3)
        elif curr == 3:
            # Leaving module screen -> back to vitals acquisition
            self.stack.setCurrentIndex(2)
        elif curr == 2:
            # Leaving vitals screen -> back to citizen selection
            self.stack.setCurrentIndex(1)
        elif curr == 1:
            # Leaving citizen screen -> back to language selection
            self.stack.setCurrentIndex(0)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        curr = self.stack.currentIndex()
        self.home_btn.setEnabled(curr != 0)
        self.back_btn.setEnabled(curr != 0)
        if hasattr(self, "new_assess_btn"):
            self.new_assess_btn.setEnabled(curr != 0)

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


AveraKioskApp = AverKioskApp


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
