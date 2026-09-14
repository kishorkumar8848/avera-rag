"""
Screen 3: Biometric Vital Signs Acquisition Screen for AVERA Kiosk.
Interactive 'One-by-One' on-demand vital sign acquisition interface:
  - Step 1: Body Temperature (MLX90614 Non-Contact IR)
  - Step 2: Pulse Oximetry (MAX30100 SpO2 & Heart Rate)
  - Step 3: Cardiac Rhythm & Single-Lead ECG (AD8232 via ADS1115)
Includes visual 3-node electrode placement diagram (RA, LA, RL) and real-time oscilloscope.
"""

from typing import Callable, Optional, List

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
        self.points: List[float] = [0.5] * 80
        self.leads_ok: bool = True
        self.is_active: bool = False
        self.status_msg: str = "Ready for ECG capture"
        self.setFixedHeight(68)

    def set_data(self, points: list, leads_ok: bool = True, is_active: bool = False, msg: str = ""):
        self.points = points
        self.leads_ok = leads_ok
        self.is_active = is_active
        if msg:
            self.status_msg = msg
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

            # 3. Waveform Trace or Status
            if not self.leads_ok:
                # Leads Off / Detached Warning
                warn_pen = QPen(QColor(239, 68, 68), 2, Qt.DashLine)
                painter.setPen(warn_pen)
                mid_y = int(h * 0.5)
                painter.drawLine(0, mid_y, w, mid_y)

                painter.setPen(QColor(248, 113, 113))
                painter.drawText(20, 26, "⚠️ ELECTRODES DETACHED — CHECK RED, YELLOW & GREEN PADS")
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

                # Overlay status label
                if self.is_active:
                    painter.setPen(QColor(56, 189, 248))  # Medical Cyan
                    painter.drawText(20, 26, "● LIVE ECG RECORDING (AD8232 — 50 Hz)")
                elif self.status_msg:
                    painter.setPen(QColor(148, 163, 184))
                    painter.drawText(20, 26, self.status_msg)

            painter.end()


class VitalsScreen(QWidget if HAS_QT else object):
    """
    Interactive touchscreen interface for acquiring patient vitals 'one-by-one':
    Body Temperature -> SpO2 & Pulse -> 3-Lead ECG.
    """

    def __init__(self, on_vitals_confirmed: Callable[[VitalsRecord], None], parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_vitals_confirmed = on_vitals_confirmed
        self.active_patient: Optional[PatientRecord] = None
        self.current_vitals: VitalsRecord = sensor_manager.get_vitals()

        # Acquisition timer counters
        self._temp_ticks = 0
        self._temp_max_ticks = 30  # 3.0s (100ms per tick)

        self._spo2_ticks = 0
        self._spo2_max_ticks = 40  # 4.0s (100ms per tick)

        self._ecg_ticks = 0
        self._ecg_max_ticks = 140  # ~5.0s (35ms per tick)

        if HAS_QT:
            self._init_ui()
            self._init_timers()

    def set_patient(self, patient: PatientRecord):
        self.active_patient = patient
        if hasattr(self, "patient_banner"):
            b = f"👤 <b>Citizen</b>: {patient.name} ({patient.age_display_badge}, {patient.gender}) • ABHA: {patient.abha_id} • Village: {patient.village}"
            self.patient_banner.setText(b)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(8)

        # 1. Compact Header Bar: Title on Left, Citizen Banner on Right
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(10)

        title_lbl = QLabel("🩺 Biometric Vital Signs Acquisition")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 800; color: #0F172A;")
        hdr_row.addWidget(title_lbl)

        hdr_row.addStretch()

        self.patient_banner = QLabel("👤 <b>Citizen</b>: Select Resident • ABHA: --")
        self.patient_banner.setStyleSheet(
            "background: #EFF6FF; color: #1E40AF; padding: 4px 12px; border-radius: 6px; "
            "font-size: 13px; border: 1px solid #BFDBFE;"
        )
        hdr_row.addWidget(self.patient_banner)
        layout.addLayout(hdr_row)

        # 2. Main 3-Column Cards Layout (Equal Width 1 : 1 : 1 Side-by-Side)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        # =====================================================================
        # CARD 1: Body Temperature (MLX90614)
        # =====================================================================
        self.temp_card = QFrame()
        self.temp_card.setObjectName("CardFrame")
        self.temp_card.setStyleSheet("QFrame#CardFrame { border-top: 4px solid #0284C7; }")
        t_layout = QVBoxLayout(self.temp_card)
        t_layout.setContentsMargins(12, 10, 12, 10)
        t_layout.setSpacing(6)

        t_hdr_row = QHBoxLayout()
        t_hdr = QLabel("🌡️ <b>Temperature</b>")
        t_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        t_hdr_row.addWidget(t_hdr)
        t_hdr_row.addStretch()
        self.temp_lock_badge = QLabel("○ Not Measured")
        self.temp_lock_badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;")
        t_hdr_row.addWidget(self.temp_lock_badge)
        t_layout.addLayout(t_hdr_row)

        t_inst = QLabel("Hold sensor 2-4 cm from forehead.")
        t_inst.setStyleSheet("font-size: 12px; color: #64748B;")
        t_layout.addWidget(t_inst)

        # Value display box
        t_val_box = QFrame()
        t_val_box.setStyleSheet("background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px; padding: 6px;")
        t_val_layout = QVBoxLayout(t_val_box)
        t_val_layout.setContentsMargins(6, 6, 6, 6)
        t_val_layout.setSpacing(4)

        self.temp_val_lbl = QLabel("--.- °F")
        self.temp_val_lbl.setAlignment(Qt.AlignCenter)
        self.temp_val_lbl.setStyleSheet("font-size: 26px; font-weight: 900; color: #0284C7;")
        t_val_layout.addWidget(self.temp_val_lbl)

        self.temp_status_lbl = QLabel("Awaiting measurement")
        self.temp_status_lbl.setAlignment(Qt.AlignCenter)
        self.temp_status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; background: #FFFFFF; padding: 2px 6px; border-radius: 4px;")
        t_val_layout.addWidget(self.temp_status_lbl)
        t_layout.addWidget(t_val_box)

        t_layout.addStretch()

        self.temp_prog = QProgressBar()
        self.temp_prog.setRange(0, 100)
        self.temp_prog.setValue(0)
        self.temp_prog.setTextVisible(False)
        self.temp_prog.setFixedHeight(5)
        self.temp_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 2px; } QProgressBar::chunk { background: #0284C7; border-radius: 2px; }")
        self.temp_prog.setVisible(False)
        t_layout.addWidget(self.temp_prog)

        self.temp_action_btn = QPushButton("▶️ Record Temp (3s)")
        self.temp_action_btn.setObjectName("NavBtn")
        self.temp_action_btn.setFixedHeight(38)
        self.temp_action_btn.setCursor(Qt.PointingHandCursor)
        self.temp_action_btn.clicked.connect(self._start_temp_reading)
        t_layout.addWidget(self.temp_action_btn)

        cards_row.addWidget(self.temp_card, 1)

        # =====================================================================
        # CARD 2: Blood Oxygen & Pulse (MAX30100)
        # =====================================================================
        self.spo2_card = QFrame()
        self.spo2_card.setObjectName("CardFrame")
        self.spo2_card.setStyleSheet("QFrame#CardFrame { border-top: 4px solid #059669; }")
        s_layout = QVBoxLayout(self.spo2_card)
        s_layout.setContentsMargins(12, 10, 12, 10)
        s_layout.setSpacing(6)

        s_hdr_row = QHBoxLayout()
        s_hdr = QLabel("💨 <b>SpO2 & Pulse</b>")
        s_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        s_hdr_row.addWidget(s_hdr)
        s_hdr_row.addStretch()
        self.spo2_lock_badge = QLabel("○ Not Measured")
        self.spo2_lock_badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;")
        s_hdr_row.addWidget(self.spo2_lock_badge)
        s_layout.addLayout(s_hdr_row)

        s_inst = QLabel("Place index finger gently on sensor.")
        s_inst.setStyleSheet("font-size: 12px; color: #64748B;")
        s_layout.addWidget(s_inst)

        # Dual value display box
        s_val_box = QFrame()
        s_val_box.setStyleSheet("background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 6px;")
        s_val_layout = QVBoxLayout(s_val_box)
        s_val_layout.setContentsMargins(6, 6, 6, 6)
        s_val_layout.setSpacing(4)

        s_dual_row = QHBoxLayout()
        s_dual_row.setSpacing(6)

        # SpO2 col
        col_sp = QVBoxLayout()
        col_sp.setSpacing(2)
        self.spo2_val_lbl = QLabel("-- %")
        self.spo2_val_lbl.setAlignment(Qt.AlignCenter)
        self.spo2_val_lbl.setStyleSheet("font-size: 24px; font-weight: 900; color: #059669;")
        col_sp.addWidget(self.spo2_val_lbl)
        self.spo2_status_lbl = QLabel("SpO2")
        self.spo2_status_lbl.setAlignment(Qt.AlignCenter)
        self.spo2_status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #065F46; background: #FFFFFF; padding: 2px 4px; border-radius: 3px;")
        col_sp.addWidget(self.spo2_status_lbl)
        s_dual_row.addLayout(col_sp)

        # HR col
        col_hr = QVBoxLayout()
        col_hr.setSpacing(2)
        self.hr_val_lbl = QLabel("-- BPM")
        self.hr_val_lbl.setAlignment(Qt.AlignCenter)
        self.hr_val_lbl.setStyleSheet("font-size: 24px; font-weight: 900; color: #DC2626;")
        col_hr.addWidget(self.hr_val_lbl)
        self.hr_status_lbl = QLabel("Pulse")
        self.hr_status_lbl.setAlignment(Qt.AlignCenter)
        self.hr_status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #991B1B; background: #FFFFFF; padding: 2px 4px; border-radius: 3px;")
        col_hr.addWidget(self.hr_status_lbl)
        s_dual_row.addLayout(col_hr)

        s_val_layout.addLayout(s_dual_row)
        s_layout.addWidget(s_val_box)

        s_layout.addStretch()

        self.spo2_prog = QProgressBar()
        self.spo2_prog.setRange(0, 100)
        self.spo2_prog.setValue(0)
        self.spo2_prog.setTextVisible(False)
        self.spo2_prog.setFixedHeight(5)
        self.spo2_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 2px; } QProgressBar::chunk { background: #059669; border-radius: 2px; }")
        self.spo2_prog.setVisible(False)
        s_layout.addWidget(self.spo2_prog)

        self.spo2_action_btn = QPushButton("▶️ Record SpO2 and Pulse (4s)")
        self.spo2_action_btn.setObjectName("NavBtn")
        self.spo2_action_btn.setFixedHeight(38)
        self.spo2_action_btn.setCursor(Qt.PointingHandCursor)
        self.spo2_action_btn.clicked.connect(self._start_spo2_reading)
        s_layout.addWidget(self.spo2_action_btn)

        cards_row.addWidget(self.spo2_card, 1)

        # =====================================================================
        # CARD 3: Cardiac Rhythm & ECG (AD8232)
        # =====================================================================
        self.ecg_card = QFrame()
        self.ecg_card.setObjectName("CardFrame")
        self.ecg_card.setStyleSheet("QFrame#CardFrame { border-top: 4px solid #7C3AED; }")
        e_layout = QVBoxLayout(self.ecg_card)
        e_layout.setContentsMargins(12, 10, 12, 10)
        e_layout.setSpacing(5)

        e_hdr_row = QHBoxLayout()
        e_hdr = QLabel("📈 <b>ECG Rhythm</b>")
        e_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        e_hdr_row.addWidget(e_hdr)
        e_hdr_row.addStretch()
        self.ecg_lock_badge = QLabel("○ Not Measured")
        self.ecg_lock_badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;")
        e_hdr_row.addWidget(self.ecg_lock_badge)
        e_layout.addLayout(e_hdr_row)

        # Compact Electrode Node Pills
        nodes_row = QHBoxLayout()
        nodes_row.setSpacing(3)
        ra_pill = QLabel("🔴 RA")
        ra_pill.setStyleSheet("font-size: 10px; font-weight: bold; color: #991B1B; background: #FEF2F2; padding: 1px 4px; border-radius: 3px;")
        nodes_row.addWidget(ra_pill)
        la_pill = QLabel("🟡 LA")
        la_pill.setStyleSheet("font-size: 10px; font-weight: bold; color: #854D0E; background: #FEFCE8; padding: 1px 4px; border-radius: 3px;")
        nodes_row.addWidget(la_pill)
        rl_pill = QLabel("🟢 RL")
        rl_pill.setStyleSheet("font-size: 10px; font-weight: bold; color: #065F46; background: #ECFDF5; padding: 1px 4px; border-radius: 3px;")
        nodes_row.addWidget(rl_pill)
        nodes_row.addStretch()

        self.lead_status_lbl = QLabel("● Leads OK")
        self.lead_status_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #059669;")
        nodes_row.addWidget(self.lead_status_lbl)
        e_layout.addLayout(nodes_row)

        # Compact ECG Oscilloscope (68px height)
        self.ecg_canvas = ECGWaveformWidget()
        self.ecg_canvas.setFixedHeight(68)
        e_layout.addWidget(self.ecg_canvas)

        e_layout.addStretch()

        self.ecg_prog = QProgressBar()
        self.ecg_prog.setRange(0, 100)
        self.ecg_prog.setValue(0)
        self.ecg_prog.setTextVisible(False)
        self.ecg_prog.setFixedHeight(5)
        self.ecg_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 2px; } QProgressBar::chunk { background: #10B981; border-radius: 2px; }")
        self.ecg_prog.setVisible(False)
        e_layout.addWidget(self.ecg_prog)

        self.ecg_action_btn = QPushButton("▶️ Record ECG (5s)")
        self.ecg_action_btn.setObjectName("NavBtn")
        self.ecg_action_btn.setFixedHeight(38)
        self.ecg_action_btn.setCursor(Qt.PointingHandCursor)
        self.ecg_action_btn.clicked.connect(self._start_ecg_reading)
        e_layout.addWidget(self.ecg_action_btn)

        cards_row.addWidget(self.ecg_card, 1)

        layout.addLayout(cards_row, stretch=1)

        # 3. Bottom Action Bar (Compact, clean row)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setObjectName("NavBtn")
        self.reset_btn.setFixedHeight(38)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset_all)
        btn_row.addWidget(self.reset_btn)

        self.skip_btn = QPushButton("⏩ Skip Vitals")
        self.skip_btn.setObjectName("NavBtn")
        self.skip_btn.setFixedHeight(38)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.clicked.connect(self._skip_vitals)
        btn_row.addWidget(self.skip_btn)

        btn_row.addStretch()

        self.confirm_btn = QPushButton("✅ Confirm Vitals and Proceed  ➔")
        self.confirm_btn.setObjectName("PrimaryBtn")
        self.confirm_btn.setFixedHeight(38)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.clicked.connect(self._confirm_and_proceed)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

    def _init_timers(self):
        # 1. Temperature acquisition timer
        self.temp_timer = QTimer(self)
        self.temp_timer.timeout.connect(self._on_temp_tick)

        # 2. SpO2 acquisition timer
        self.spo2_timer = QTimer(self)
        self.spo2_timer.timeout.connect(self._on_spo2_tick)

        # 3. ECG recording timer
        self.ecg_timer = QTimer(self)
        self.ecg_timer.timeout.connect(self._on_ecg_tick)

        # 4. Background sensor check timer (Checks leads-off status every 300ms)
        self.leads_timer = QTimer(self)
        self.leads_timer.timeout.connect(self._check_leads_status)
        self.leads_timer.start(300)

    def _check_leads_status(self):
        """Monitors real-time sensor connection and electrode attachment status."""
        v = sensor_manager.get_vitals()
        hw_ad8232 = v.hardware_connected.get("AD8232", False) or v.hardware_connected.get("ADS1115", False)
        if hw_ad8232:
            if v.ecg_leads_ok:
                self.lead_status_lbl.setText("● Sensor Ready (Leads OK)")
                self.lead_status_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #059669;")
            else:
                self.lead_status_lbl.setText("● Connected (Place Leads)")
                self.lead_status_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #2563EB;")
        else:
            self.lead_status_lbl.setText("○ Sim Mode")
            self.lead_status_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748B;")

    # -------------------------------------------------------------------------
    # STEP 1: TEMPERATURE ON-DEMAND MEASUREMENT
    # -------------------------------------------------------------------------

    def _start_temp_reading(self):
        self._temp_ticks = 0
        self.temp_prog.setValue(0)
        self.temp_prog.setVisible(True)
        self.temp_action_btn.setEnabled(False)
        self.temp_action_btn.setText("⏳ Measuring Forehead Temp (3s)...")
        self.temp_val_lbl.setText("Reading...")
        self.temp_timer.start(100)

    def _on_temp_tick(self):
        self._temp_ticks += 1
        pct = int((self._temp_ticks / self._temp_max_ticks) * 100)
        self.temp_prog.setValue(min(100, pct))

        if self._temp_ticks >= self._temp_max_ticks:
            self.temp_timer.stop()
            self.temp_prog.setVisible(False)
            f, c, stat, sim = sensor_manager.measure_temperature_now(duration_sec=0.2)
            self.current_vitals.temperature_f = f
            self.current_vitals.temperature_c = c
            self.current_vitals.temp_measured = True

            self.temp_val_lbl.setText(f"{f:.1f} °F")
            self.temp_status_lbl.setText(f"{stat} ({c:.1f} °C)")

            if f >= 100.4:
                self.temp_status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #991B1B; background: #FEE2E2; padding: 6px 12px; border-radius: 6px;")
            else:
                self.temp_status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #065F46; background: #ECFDF5; padding: 6px 12px; border-radius: 6px;")

            self.temp_lock_badge.setText("✅ Recorded")
            self.temp_lock_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #065F46; background: #ECFDF5; padding: 4px 8px; border-radius: 4px;")
            self.temp_action_btn.setText("🔄 Retake Temperature")
            self.temp_action_btn.setEnabled(True)
            self._update_confirm_button_state()

    # -------------------------------------------------------------------------
    # STEP 2: SPO2 & PULSE ON-DEMAND MEASUREMENT
    # -------------------------------------------------------------------------

    def _start_spo2_reading(self):
        self._spo2_ticks = 0
        self.spo2_prog.setValue(0)
        self.spo2_prog.setVisible(True)
        self.spo2_action_btn.setEnabled(False)
        self.spo2_action_btn.setText("⏳ Measuring SpO2 and Pulse (4s)...")
        self.spo2_val_lbl.setText("Reading...")
        self.hr_val_lbl.setText("Reading...")
        self.spo2_timer.start(100)

    def _on_spo2_tick(self):
        self._spo2_ticks += 1
        pct = int((self._spo2_ticks / self._spo2_max_ticks) * 100)
        self.spo2_prog.setValue(min(100, pct))

        if self._spo2_ticks >= self._spo2_max_ticks:
            self.spo2_timer.stop()
            self.spo2_prog.setVisible(False)
            spo2, hr, sp_stat, hr_stat, sim = sensor_manager.measure_spo2_pulse_now(duration_sec=0.2)
            self.current_vitals.spo2_percent = spo2
            self.current_vitals.heart_rate_bpm = hr
            self.current_vitals.spo2_measured = True

            self.spo2_val_lbl.setText(f"{spo2} %")
            self.spo2_status_lbl.setText(f"SpO2: {sp_stat}")

            self.hr_val_lbl.setText(f"{hr} BPM")
            self.hr_status_lbl.setText(f"Pulse: {hr_stat}")

            self.spo2_lock_badge.setText("✅ Recorded")
            self.spo2_lock_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #065F46; background: #ECFDF5; padding: 4px 8px; border-radius: 4px;")
            self.spo2_action_btn.setText("🔄 Retake SpO2 and Pulse")
            self.spo2_action_btn.setEnabled(True)
            self._update_confirm_button_state()

    # -------------------------------------------------------------------------
    # STEP 3: ECG RHYTHM ON-DEMAND MEASUREMENT
    # -------------------------------------------------------------------------

    def _start_ecg_reading(self):
        self._ecg_ticks = 0
        self.ecg_prog.setValue(0)
        self.ecg_prog.setVisible(True)
        self.ecg_action_btn.setEnabled(False)
        self.ecg_action_btn.setText("⏳ Recording Rhythm Strip (5s)...")
        self.ecg_canvas.is_active = True
        self.ecg_timer.start(35)

    def _on_ecg_tick(self):
        self._ecg_ticks += 1
        pct = int((self._ecg_ticks / self._ecg_max_ticks) * 100)
        self.ecg_prog.setValue(min(100, pct))

        # Update real-time oscilloscope canvas on each tick
        v = sensor_manager.get_vitals()
        self.ecg_canvas.set_data(v.ecg_waveform, v.ecg_leads_ok, is_active=True)

        if self._ecg_ticks >= self._ecg_max_ticks:
            self.ecg_timer.stop()
            self.ecg_prog.setVisible(False)
            waveform, status, leads_ok, bpm, sim = sensor_manager.measure_ecg_now(duration_sec=0.5)
            self.current_vitals.ecg_measured = True
            self.current_vitals.ecg_waveform = waveform
            self.current_vitals.ecg_leads_ok = leads_ok
            self.current_vitals.heart_rate_bpm = bpm

            self.ecg_canvas.set_data(
                waveform, leads_ok, is_active=False,
                msg=f"✅ {status.upper()} ({bpm} BPM) — 5s RHYTHM STRIP LOCKED"
            )

            self.ecg_lock_badge.setText("✅ Recorded")
            self.ecg_lock_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #065F46; background: #ECFDF5; padding: 4px 8px; border-radius: 4px;")
            self.ecg_action_btn.setText("🔄 Retake ECG Strip")
            self.ecg_action_btn.setEnabled(True)
            self._update_confirm_button_state()

    # -------------------------------------------------------------------------
    # RESET & CONFIRMATION NAVIGATION
    # -------------------------------------------------------------------------

    def _update_confirm_button_state(self):
        """Highlights the confirmation button once any measurement is taken."""
        if self.current_vitals.temp_measured or self.current_vitals.spo2_measured or self.current_vitals.ecg_measured:
            self.confirm_btn.setStyleSheet(
                "background-color: #10B981; color: white; font-weight: bold; border-radius: 8px; font-size: 16px; padding: 12px 24px;"
            )

    def _reset_all(self):
        """Resets all recorded cards for a clean re-examination."""
        sensor_manager.reset_readings()
        self.current_vitals = sensor_manager.get_vitals()

        self.temp_val_lbl.setText("--.- °F")
        self.temp_status_lbl.setText("Awaiting measurement")
        self.temp_status_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: #F8FAFC; padding: 6px 12px; border-radius: 6px;")
        self.temp_lock_badge.setText("○ Not Measured")
        self.temp_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        self.temp_action_btn.setText("▶️ Take Temperature Reading (3s)")

        self.spo2_val_lbl.setText("-- %")
        self.spo2_status_lbl.setText("SpO2 Saturation")
        self.hr_val_lbl.setText("-- BPM")
        self.hr_status_lbl.setText("Heart Rate / Pulse")
        self.spo2_lock_badge.setText("○ Not Measured")
        self.spo2_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        self.spo2_action_btn.setText("▶️ Take SpO2 and Pulse Reading (4s)")

        self.ecg_canvas.set_data([0.5] * 80, True, is_active=False, msg="Ready for ECG capture")
        self.ecg_lock_badge.setText("○ Not Measured")
        self.ecg_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        self.ecg_action_btn.setText("▶️ Record ECG Rhythm (5s)")

        self.confirm_btn.setStyleSheet("")

    def _skip_vitals(self):
        """Skips vital sign recording and proceeds with general consultation."""
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(None)

    def _confirm_and_proceed(self):
        """Confirms recorded vitals and navigates to module selection."""
        has_any = (
            self.current_vitals.temp_measured or
            self.current_vitals.spo2_measured or
            self.current_vitals.ecg_measured
        )
        v = self.current_vitals if has_any else None
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(v)
