"""
Screen 3: Biometric Vital Signs Acquisition Screen for AVERA Kiosk.
Displays live telemetry and medical waveforms from 4 integrated Jetson sensors:
  - MLX90614 Non-Contact IR Thermometer (Body Temp °F / °C)
  - MAX30100 Pulse Oximeter (SpO2 % & Heart Rate BPM)
  - AD8232 Single-Lead ECG (via ADS1115 A0 + GPIO Leads-Off detection)
"""

from typing import Callable, Optional

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QPainter, QPen, QColor, QBrush, QTimer, Qt, HAS_QT
)

from app.hardware.sensor_manager import sensor_manager, VitalsRecord
from app.safety.patient_registry import PatientRecord


class ECGWaveformWidget(QWidget if HAS_QT else object):
    """
    Hospital monitor style real-time ECG oscilloscope canvas.
    Renders rolling green biopotential trace against a subtle medical grid.
    """

    def __init__(self, parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.points = [0.5] * 80
        self.leads_ok = True
        self.setMinimumHeight(140)

    def set_data(self, points: list, leads_ok: bool = True):
        self.points = points
        self.leads_ok = leads_ok
        if HAS_QT:
            self.update()

    if HAS_QT:
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            w = self.width()
            h = self.height()

            # 1. Dark Hospital Monitor Background
            painter.fillRect(0, 0, w, h, QColor(15, 23, 42))

            # 2. Subtle Medical Oscilloscope Grid Lines
            grid_pen = QPen(QColor(30, 41, 59), 1, Qt.DotLine)
            painter.setPen(grid_pen)
            step_x = 24
            step_y = 20
            for x in range(0, w, step_x):
                painter.drawLine(x, 0, x, h)
            for y in range(0, h, step_y):
                painter.drawLine(0, y, w, y)

            # 3. Waveform Trace
            if not self.leads_ok:
                # Flatline / Lead Off Warning
                warn_pen = QPen(QColor(239, 68, 68), 2, Qt.DashLine)
                painter.setPen(warn_pen)
                mid_y = int(h * 0.5)
                painter.drawLine(0, mid_y, w, mid_y)

                painter.setPen(QColor(248, 113, 113))
                painter.drawText(20, 24, "⚠️ ELECTRODES DETACHED / LEADS OFF")
            else:
                trace_pen = QPen(QColor(16, 185, 129), 2.5)  # Bright Medical Emerald
                painter.setPen(trace_pen)

                n = len(self.points)
                if n > 1:
                    dx = w / (n - 1)
                    for i in range(n - 1):
                        x1 = int(i * dx)
                        y1 = int(h - (self.points[i] * h))
                        x2 = int((i + 1) * dx)
                        y2 = int(h - (self.points[i + 1] * h))
                        painter.drawLine(x1, y1, x2, y2)

            painter.end()


class VitalsScreen(QWidget if HAS_QT else object):
    """
    Dedicated touchscreen interface for acquiring patient vitals
    before proceeding to clinical symptoms analysis.
    """

    def __init__(self, on_vitals_confirmed: Callable[[VitalsRecord], None], parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_vitals_confirmed = on_vitals_confirmed
        self.active_patient: Optional[PatientRecord] = None
        self.recorded_vitals: Optional[VitalsRecord] = None
        self.is_capturing = False
        self.capture_seconds_left = 5

        if HAS_QT:
            self._init_ui()
            self._init_timers()

    def set_patient(self, patient: PatientRecord):
        self.active_patient = patient
        if hasattr(self, "patient_banner"):
            b = f"👤 <b>{patient.name}</b> ({patient.age_display_badge}, {patient.gender}) • ABHA: {patient.abha_id} • {patient.village}"
            self.patient_banner.setText(b)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 24)
        layout.setSpacing(16)

        # 1. Patient Profile Info Strip
        self.patient_banner = QLabel("👤 <b>Citizen</b>: Select Resident • ABHA: --")
        self.patient_banner.setStyleSheet(
            "background: #EFF6FF; color: #1E40AF; padding: 10px 16px; border-radius: 8px; "
            "font-size: 15px; border: 1px solid #BFDBFE;"
        )
        layout.addWidget(self.patient_banner)

        # Header Title
        h_box = QWidget()
        h_layout = QVBoxLayout(h_box)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)
        title = QLabel("Biometric Vital Signs Acquisition")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;")
        h_layout.addWidget(title)
        subtitle = QLabel("Live telemetry from non-contact thermometer, pulse oximeter, and single-lead ECG")
        subtitle.setStyleSheet("font-size: 15px; color: #64748B; font-weight: 500;")
        h_layout.addWidget(subtitle)
        layout.addWidget(h_box)

        # 2. Vitals Cards Grid (2x2)
        grid = QGridLayout()
        grid.setSpacing(16)

        # Card 1: Temperature (MLX90614)
        self.temp_card = QFrame()
        self.temp_card.setObjectName("CardFrame")
        t_layout = QVBoxLayout(self.temp_card)
        t_layout.setContentsMargins(20, 16, 20, 16)
        t_layout.setSpacing(8)

        t_hdr = QLabel("🌡️ Body Temperature (MLX90614)")
        t_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #475569;")
        t_layout.addWidget(t_hdr)

        self.temp_val_lbl = QLabel("98.6 °F")
        self.temp_val_lbl.setStyleSheet("font-size: 34px; font-weight: 900; color: #0284C7;")
        t_layout.addWidget(self.temp_val_lbl)

        self.temp_badge = QLabel("Normal (37.0 °C)")
        self.temp_badge.setStyleSheet(
            "background: #ECFDF5; color: #065F46; font-size: 13px; font-weight: 700; "
            "padding: 4px 10px; border-radius: 6px;"
        )
        t_layout.addWidget(self.temp_badge)

        self.temp_hw_status = QLabel("● Sensor Ready (0x5A)")
        self.temp_hw_status.setStyleSheet("font-size: 12px; color: #64748B;")
        t_layout.addWidget(self.temp_hw_status)
        grid.addWidget(self.temp_card, 0, 0)

        # Card 2: SpO2 Oxygen Saturation (MAX30100)
        self.spo2_card = QFrame()
        self.spo2_card.setObjectName("CardFrame")
        s_layout = QVBoxLayout(self.spo2_card)
        s_layout.setContentsMargins(20, 16, 20, 16)
        s_layout.setSpacing(8)

        s_hdr = QLabel("💨 Oxygen Saturation SpO2 (MAX30100)")
        s_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #475569;")
        s_layout.addWidget(s_hdr)

        self.spo2_val_lbl = QLabel("98 %")
        self.spo2_val_lbl.setStyleSheet("font-size: 34px; font-weight: 900; color: #059669;")
        s_layout.addWidget(self.spo2_val_lbl)

        self.spo2_badge = QLabel("Adequate Saturation (≥95%)")
        self.spo2_badge.setStyleSheet(
            "background: #ECFDF5; color: #065F46; font-size: 13px; font-weight: 700; "
            "padding: 4px 10px; border-radius: 6px;"
        )
        s_layout.addWidget(self.spo2_badge)

        self.spo2_hw_status = QLabel("● Sensor Ready (0x57)")
        self.spo2_hw_status.setStyleSheet("font-size: 12px; color: #64748B;")
        s_layout.addWidget(self.spo2_hw_status)
        grid.addWidget(self.spo2_card, 0, 1)

        # Card 3: Heart Rate / Pulse
        self.hr_card = QFrame()
        self.hr_card.setObjectName("CardFrame")
        hr_layout = QVBoxLayout(self.hr_card)
        hr_layout.setContentsMargins(20, 16, 20, 16)
        hr_layout.setSpacing(8)

        hr_hdr = QLabel("🫀 Heart Rate / Pulse")
        hr_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #475569;")
        hr_layout.addWidget(hr_hdr)

        self.hr_val_lbl = QLabel("74 BPM")
        self.hr_val_lbl.setStyleSheet("font-size: 34px; font-weight: 900; color: #DC2626;")
        hr_layout.addWidget(self.hr_val_lbl)

        self.hr_badge = QLabel("Normal Sinus (60-100 BPM)")
        self.hr_badge.setStyleSheet(
            "background: #ECFDF5; color: #065F46; font-size: 13px; font-weight: 700; "
            "padding: 4px 10px; border-radius: 6px;"
        )
        hr_layout.addWidget(self.hr_badge)

        self.hr_hw_status = QLabel("● R-wave Sync Active")
        self.hr_hw_status.setStyleSheet("font-size: 12px; color: #64748B;")
        hr_layout.addWidget(self.hr_hw_status)
        grid.addWidget(self.hr_card, 1, 0)

        # Card 4: ECG Monitor (AD8232 via ADS1115)
        self.ecg_card = QFrame()
        self.ecg_card.setObjectName("CardFrame")
        e_layout = QVBoxLayout(self.ecg_card)
        e_layout.setContentsMargins(18, 14, 18, 14)
        e_layout.setSpacing(6)

        e_hdr_row = QHBoxLayout()
        e_hdr = QLabel("📈 Single-Lead ECG Monitor (AD8232 via ADS1115)")
        e_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #475569;")
        e_hdr_row.addWidget(e_hdr)
        e_hdr_row.addStretch()

        self.lead_status_badge = QLabel("● Leads Connected (LO-/LO+ OK)")
        self.lead_status_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669;")
        e_hdr_row.addWidget(self.lead_status_badge)
        e_layout.addLayout(e_hdr_row)

        self.ecg_canvas = ECGWaveformWidget()
        e_layout.addWidget(self.ecg_canvas)

        grid.addWidget(self.ecg_card, 1, 1)

        layout.addLayout(grid, stretch=1)

        # 3. Capture Progress Bar (for 5s stabilized recording)
        self.capture_prog = QProgressBar()
        self.capture_prog.setRange(0, 5)
        self.capture_prog.setValue(0)
        self.capture_prog.setTextVisible(False)
        self.capture_prog.setFixedHeight(8)
        self.capture_prog.setStyleSheet(
            "QProgressBar { background: #E2E8F0; border-radius: 4px; } "
            "QProgressBar::chunk { background: #2563EB; border-radius: 4px; }"
        )
        self.capture_prog.setVisible(False)
        layout.addWidget(self.capture_prog)

        # 4. Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.record_btn = QPushButton("▶️ Record Vitals (5s Auto-Lock)")
        self.record_btn.setObjectName("NavBtn")
        self.record_btn.setMinimumHeight(52)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.clicked.connect(self._start_capture)
        btn_row.addWidget(self.record_btn)

        self.skip_btn = QPushButton("⏩ Skip Vitals")
        self.skip_btn.setObjectName("NavBtn")
        self.skip_btn.setMinimumHeight(52)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.clicked.connect(self._skip_vitals)
        btn_row.addWidget(self.skip_btn)

        btn_row.addStretch()

        self.confirm_btn = QPushButton("✅ Confirm Vitals & Proceed to Assessment  ➔")
        self.confirm_btn.setObjectName("PrimaryBtn")
        self.confirm_btn.setMinimumHeight(52)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self._confirm_and_proceed)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

    def _init_timers(self):
        # 30 Hz Refresh Timer for Live ECG Oscilloscope and Vitals
        self.live_timer = QTimer(self)
        self.live_timer.timeout.connect(self._update_live_vitals)
        self.live_timer.start(35)

        # 1-second countdown timer for 5s stabilized vital capture
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self._on_capture_tick)

    def _update_live_vitals(self):
        v = sensor_manager.get_vitals()
        self.recorded_vitals = v

        # 1. Update Temperature
        self.temp_val_lbl.setText(f"{v.temperature_f:.1f} °F")
        self.temp_badge.setText(f"{v.temperature_status} ({v.temperature_c:.1f} °C)")
        if v.temperature_f >= 100.4:
            self.temp_badge.setStyleSheet("background: #FEE2E2; color: #991B1B; font-weight: bold; padding: 4px 10px; border-radius: 6px;")
        else:
            self.temp_badge.setStyleSheet("background: #ECFDF5; color: #065F46; font-weight: bold; padding: 4px 10px; border-radius: 6px;")

        # 2. Update SpO2
        self.spo2_val_lbl.setText(f"{v.spo2_percent} %")
        self.spo2_badge.setText(v.spo2_status)
        if v.spo2_percent < 94:
            self.spo2_badge.setStyleSheet("background: #FEE2E2; color: #991B1B; font-weight: bold; padding: 4px 10px; border-radius: 6px;")
        else:
            self.spo2_badge.setStyleSheet("background: #ECFDF5; color: #065F46; font-weight: bold; padding: 4px 10px; border-radius: 6px;")

        # 3. Update Heart Rate
        self.hr_val_lbl.setText(f"{v.heart_rate_bpm} BPM")
        self.hr_badge.setText(v.pulse_status)

        # 4. Update ECG Oscilloscope Canvas
        self.ecg_canvas.set_data(v.ecg_waveform, v.ecg_leads_ok)
        if v.ecg_leads_ok:
            self.lead_status_badge.setText("● Leads Connected (LO-/LO+ OK)")
            self.lead_status_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669;")
        else:
            self.lead_status_badge.setText("⚠️ Leads Detached (Electrodes Off)")
            self.lead_status_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #DC2626;")

        # Sensor connection hardware labels
        hw = v.hardware_connected
        self.temp_hw_status.setText("● Hardware Connected (0x5A)" if hw.get("MLX90614") else "○ Standby / Live Baseline")
        self.spo2_hw_status.setText("● Hardware Connected (0x57)" if hw.get("MAX30100") else "○ Standby / Live Baseline")

    def _start_capture(self):
        self.is_capturing = True
        self.capture_seconds_left = 5
        self.capture_prog.setValue(0)
        self.capture_prog.setVisible(True)
        self.record_btn.setText(f"⏳ Locking Readings ({self.capture_seconds_left}s)...")
        self.record_btn.setEnabled(False)
        self.capture_timer.start(1000)

    def _on_capture_tick(self):
        self.capture_seconds_left -= 1
        self.capture_prog.setValue(5 - self.capture_seconds_left)
        if self.capture_seconds_left <= 0:
            self.capture_timer.stop()
            self.is_capturing = False
            self.capture_prog.setVisible(False)
            self.record_btn.setText("🔄 Retake Vitals (5s)")
            self.record_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet(
                "background-color: #10B981; color: white; font-weight: bold; border-radius: 8px;"
            )
        else:
            self.record_btn.setText(f"⏳ Locking Readings ({self.capture_seconds_left}s)...")

    def _skip_vitals(self):
        v = self.recorded_vitals or VitalsRecord()
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(v)

    def _confirm_and_proceed(self):
        v = self.recorded_vitals or sensor_manager.get_vitals()
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(v)
