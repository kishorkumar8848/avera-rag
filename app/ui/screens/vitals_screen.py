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
        self.setMinimumHeight(150)

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
        layout.setContentsMargins(36, 16, 36, 20)
        layout.setSpacing(14)

        # 1. Patient Profile Info Strip
        self.patient_banner = QLabel("👤 <b>Citizen</b>: Select Resident • ABHA: --")
        self.patient_banner.setStyleSheet(
            "background: #EFF6FF; color: #1E40AF; padding: 10px 16px; border-radius: 8px; "
            "font-size: 15px; border: 1px solid #BFDBFE;"
        )
        layout.addWidget(self.patient_banner)

        # 2. Header & Step Instructions
        h_box = QWidget()
        h_layout = QVBoxLayout(h_box)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(3)

        title = QLabel("Biometric Vital Signs Acquisition")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;")
        h_layout.addWidget(title)

        subtitle = QLabel("Click 'Take Reading' to measure each vital sign one by one. Follow the ECG node guide for electrode placement.")
        subtitle.setStyleSheet("font-size: 14px; color: #64748B; font-weight: 500;")
        h_layout.addWidget(subtitle)
        layout.addWidget(h_box)

        # 3. Main Split Content (Left: Temp & SpO2 Cards, Right: ECG & Electrode Guide)
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Left Column (Temp + SpO2)
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        # ---------------------------------------------------------------------
        # Card 1: Body Temperature (MLX90614 Non-Contact IR)
        # ---------------------------------------------------------------------
        self.temp_card = QFrame()
        self.temp_card.setObjectName("CardFrame")
        t_layout = QVBoxLayout(self.temp_card)
        t_layout.setContentsMargins(20, 16, 20, 16)
        t_layout.setSpacing(8)

        t_hdr_row = QHBoxLayout()
        t_hdr = QLabel("🌡️ <b>Step 1: Body Temperature</b>")
        t_hdr.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        t_hdr_row.addWidget(t_hdr)
        t_hdr_row.addStretch()

        self.temp_lock_badge = QLabel("○ Not Measured")
        self.temp_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        t_hdr_row.addWidget(self.temp_lock_badge)
        t_layout.addLayout(t_hdr_row)

        t_inst = QLabel("👉 Hold infrared sensor 2-4 cm from center of patient's forehead.")
        t_inst.setStyleSheet("font-size: 13px; color: #475569; font-weight: 500;")
        t_layout.addWidget(t_inst)

        t_val_row = QHBoxLayout()
        self.temp_val_lbl = QLabel("--.- °F")
        self.temp_val_lbl.setStyleSheet("font-size: 32px; font-weight: 900; color: #0284C7;")
        t_val_row.addWidget(self.temp_val_lbl)

        self.temp_status_lbl = QLabel("Awaiting measurement")
        self.temp_status_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B; background: #F8FAFC; padding: 6px 12px; border-radius: 6px;")
        t_val_row.addWidget(self.temp_status_lbl)
        t_val_row.addStretch()
        t_layout.addLayout(t_val_row)

        self.temp_prog = QProgressBar()
        self.temp_prog.setRange(0, 100)
        self.temp_prog.setValue(0)
        self.temp_prog.setTextVisible(False)
        self.temp_prog.setFixedHeight(6)
        self.temp_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 3px; } QProgressBar::chunk { background: #0284C7; border-radius: 3px; }")
        self.temp_prog.setVisible(False)
        t_layout.addWidget(self.temp_prog)

        self.temp_action_btn = QPushButton("▶️ Take Temperature Reading (3s)")
        self.temp_action_btn.setObjectName("NavBtn")
        self.temp_action_btn.setMinimumHeight(44)
        self.temp_action_btn.setCursor(Qt.PointingHandCursor)
        self.temp_action_btn.clicked.connect(self._start_temp_reading)
        t_layout.addWidget(self.temp_action_btn)

        left_col.addWidget(self.temp_card)

        # ---------------------------------------------------------------------
        # Card 2: Blood Oxygen & Pulse (MAX30100)
        # ---------------------------------------------------------------------
        self.spo2_card = QFrame()
        self.spo2_card.setObjectName("CardFrame")
        s_layout = QVBoxLayout(self.spo2_card)
        s_layout.setContentsMargins(20, 16, 20, 16)
        s_layout.setSpacing(8)

        s_hdr_row = QHBoxLayout()
        s_hdr = QLabel("💨 <b>Step 2: Blood Oxygen & Pulse</b>")
        s_hdr.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        s_hdr_row.addWidget(s_hdr)
        s_hdr_row.addStretch()

        self.spo2_lock_badge = QLabel("○ Not Measured")
        self.spo2_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        s_hdr_row.addWidget(self.spo2_lock_badge)
        s_layout.addLayout(s_hdr_row)

        s_inst = QLabel("👉 Place patient's index finger gently on the red optical sensor.")
        s_inst.setStyleSheet("font-size: 13px; color: #475569; font-weight: 500;")
        s_layout.addWidget(s_inst)

        s_val_row = QHBoxLayout()
        s_val_row.setSpacing(14)

        v_box1 = QVBoxLayout()
        self.spo2_val_lbl = QLabel("-- %")
        self.spo2_val_lbl.setStyleSheet("font-size: 32px; font-weight: 900; color: #059669;")
        self.spo2_status_lbl = QLabel("SpO2 Saturation")
        self.spo2_status_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        v_box1.addWidget(self.spo2_val_lbl)
        v_box1.addWidget(self.spo2_status_lbl)
        s_val_row.addLayout(v_box1)

        v_box2 = QVBoxLayout()
        self.hr_val_lbl = QLabel("-- BPM")
        self.hr_val_lbl.setStyleSheet("font-size: 32px; font-weight: 900; color: #DC2626;")
        self.hr_status_lbl = QLabel("Heart Rate / Pulse")
        self.hr_status_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        v_box2.addWidget(self.hr_val_lbl)
        v_box2.addWidget(self.hr_status_lbl)
        s_val_row.addLayout(v_box2)

        s_val_row.addStretch()
        s_layout.addLayout(s_val_row)

        self.spo2_prog = QProgressBar()
        self.spo2_prog.setRange(0, 100)
        self.spo2_prog.setValue(0)
        self.spo2_prog.setTextVisible(False)
        self.spo2_prog.setFixedHeight(6)
        self.spo2_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 3px; } QProgressBar::chunk { background: #059669; border-radius: 3px; }")
        self.spo2_prog.setVisible(False)
        s_layout.addWidget(self.spo2_prog)

        self.spo2_action_btn = QPushButton("▶️ Take SpO2 & Pulse Reading (4s)")
        self.spo2_action_btn.setObjectName("NavBtn")
        self.spo2_action_btn.setMinimumHeight(44)
        self.spo2_action_btn.setCursor(Qt.PointingHandCursor)
        self.spo2_action_btn.clicked.connect(self._start_spo2_reading)
        s_layout.addWidget(self.spo2_action_btn)

        left_col.addWidget(self.spo2_card)

        content_row.addLayout(left_col, stretch=4)

        # ---------------------------------------------------------------------
        # Right Column (ECG Rhythm & Node Placement Guide)
        # ---------------------------------------------------------------------
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        self.ecg_card = QFrame()
        self.ecg_card.setObjectName("CardFrame")
        e_layout = QVBoxLayout(self.ecg_card)
        e_layout.setContentsMargins(20, 16, 20, 16)
        e_layout.setSpacing(10)

        # Header Row
        e_hdr_row = QHBoxLayout()
        e_hdr = QLabel("📈 <b>Step 3: Cardiac Rhythm & ECG Monitor (AD8232)</b>")
        e_hdr.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        e_hdr_row.addWidget(e_hdr)
        e_hdr_row.addStretch()

        self.ecg_lock_badge = QLabel("○ Not Measured")
        self.ecg_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        e_hdr_row.addWidget(self.ecg_lock_badge)
        e_layout.addLayout(e_hdr_row)

        # ---------------------------------------------------------------------
        # VISUAL ELECTRODE PLACEMENT GUIDE (3-LEAD EINTHOVEN TRIANGLE)
        # ---------------------------------------------------------------------
        guide_box = QFrame()
        guide_box.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px;")
        g_layout = QVBoxLayout(guide_box)
        g_layout.setContentsMargins(10, 8, 10, 8)
        g_layout.setSpacing(6)

        g_title_row = QHBoxLayout()
        g_title = QLabel("📍 <b>3-Node Electrode Placement Guide:</b>")
        g_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #1E293B;")
        g_title_row.addWidget(g_title)
        g_title_row.addStretch()

        self.lead_status_lbl = QLabel("● Leads Connected (LO+/LO- OK)")
        self.lead_status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669;")
        g_title_row.addWidget(self.lead_status_lbl)
        g_layout.addLayout(g_title_row)

        nodes_row = QHBoxLayout()
        nodes_row.setSpacing(8)

        # Node 1: RA (Red)
        ra_box = QLabel("🔴 <b>RA (Red Lead)</b><br/>Right Upper Chest<br/><i>(Below Collarbone)</i>")
        ra_box.setStyleSheet("background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; padding: 6px 10px; border-radius: 6px; font-size: 12px;")
        nodes_row.addWidget(ra_box)

        # Node 2: LA (Yellow)
        la_box = QLabel("🟡 <b>LA (Yellow Lead)</b><br/>Left Upper Chest<br/><i>(Below Collarbone)</i>")
        la_box.setStyleSheet("background: #FEFCE8; color: #854D0E; border: 1px solid #FEF08A; padding: 6px 10px; border-radius: 6px; font-size: 12px;")
        nodes_row.addWidget(la_box)

        # Node 3: RL (Green)
        rl_box = QLabel("🟢 <b>RL (Green Lead)</b><br/>Right Lower Flank<br/><i>(Reference Ground)</i>")
        rl_box.setStyleSheet("background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; padding: 6px 10px; border-radius: 6px; font-size: 12px;")
        nodes_row.addWidget(rl_box)

        g_layout.addLayout(nodes_row)
        e_layout.addWidget(guide_box)

        # ECG Oscilloscope Screen
        self.ecg_canvas = ECGWaveformWidget()
        e_layout.addWidget(self.ecg_canvas)

        # Progress bar
        self.ecg_prog = QProgressBar()
        self.ecg_prog.setRange(0, 100)
        self.ecg_prog.setValue(0)
        self.ecg_prog.setTextVisible(False)
        self.ecg_prog.setFixedHeight(6)
        self.ecg_prog.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 3px; } QProgressBar::chunk { background: #10B981; border-radius: 3px; }")
        self.ecg_prog.setVisible(False)
        e_layout.addWidget(self.ecg_prog)

        # ECG Action Button
        self.ecg_action_btn = QPushButton("▶️ Record ECG Rhythm (5s)")
        self.ecg_action_btn.setObjectName("NavBtn")
        self.ecg_action_btn.setMinimumHeight(44)
        self.ecg_action_btn.setCursor(Qt.PointingHandCursor)
        self.ecg_action_btn.clicked.connect(self._start_ecg_reading)
        e_layout.addWidget(self.ecg_action_btn)

        right_col.addWidget(self.ecg_card)
        content_row.addLayout(right_col, stretch=5)

        layout.addLayout(content_row, stretch=1)

        # 4. Bottom Action Bar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.reset_btn = QPushButton("🔄 Reset Readings")
        self.reset_btn.setObjectName("NavBtn")
        self.reset_btn.setMinimumHeight(48)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset_all)
        btn_row.addWidget(self.reset_btn)

        self.skip_btn = QPushButton("⏩ Skip Vitals & Proceed")
        self.skip_btn.setObjectName("NavBtn")
        self.skip_btn.setMinimumHeight(48)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.clicked.connect(self._skip_vitals)
        btn_row.addWidget(self.skip_btn)

        btn_row.addStretch()

        self.confirm_btn = QPushButton("✅ Confirm Vitals & Proceed to Assessment  ➔")
        self.confirm_btn.setObjectName("PrimaryBtn")
        self.confirm_btn.setMinimumHeight(48)
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
        """Monitors real-time electrode attachment status."""
        v = sensor_manager.get_vitals()
        if v.ecg_leads_ok:
            self.lead_status_lbl.setText("● Electrodes Connected (Ready)")
            self.lead_status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #059669;")
        else:
            self.lead_status_lbl.setText("⚠️ Electrodes Detached (Check Pad Contact)")
            self.lead_status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #DC2626;")

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
        self.spo2_action_btn.setText("⏳ Measuring SpO2 & Pulse (4s)...")
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
            self.spo2_action_btn.setText("🔄 Retake SpO2 & Pulse")
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
        self.spo2_action_btn.setText("▶️ Take SpO2 & Pulse Reading (4s)")

        self.ecg_canvas.set_data([0.5] * 80, True, is_active=False, msg="Ready for ECG capture")
        self.ecg_lock_badge.setText("○ Not Measured")
        self.ecg_lock_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        self.ecg_action_btn.setText("▶️ Record ECG Rhythm (5s)")

        self.confirm_btn.setStyleSheet("")

    def _skip_vitals(self):
        """Skips vital sign recording and proceeds with general consultation."""
        v = self.current_vitals or sensor_manager.get_vitals()
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(v)

    def _confirm_and_proceed(self):
        """Confirms recorded vitals and navigates to module selection."""
        v = self.current_vitals or sensor_manager.get_vitals()
        if self.on_vitals_confirmed:
            self.on_vitals_confirmed(v)
