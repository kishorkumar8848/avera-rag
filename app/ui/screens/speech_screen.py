"""
Speech Assistant Screen for Vyoma Kiosk.
Provides push-to-talk voice recording, dynamic status indicators,
ASHA village citizen selection, structured clinical guidance display,
USB clinical slip printing, and assessment lifecycle management.
"""

from typing import Optional, Dict, Any, List

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, Qt, QThreadPool, QTimer, Slot,
    QLineEdit, QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, HAS_QT
)

from app.core.config import settings
from app.core.logging import logger
from app.hardware.audio import AudioRecorder
from app.models.bhashini_tts import tts_service
from app.ui.workers import SpeechPipelineWorker
from app.rag.hybrid_retriever import HybridRetriever
from app.safety.patient_registry import patient_registry, PatientRecord
from app.ui.report_printer import print_clinical_report


class CitizenSearchDialog(QDialog if HAS_QT else object):
    """
    Interactive search dialog allowing ASHA workers to quickly search
    village residents by typing Name (e.g. 'kishor'), Age ('50'), Phone, or ABHA ID.
    """

    def __init__(self, parent=None, on_selected=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_selected = on_selected
        self.selected_patient: Optional[PatientRecord] = None

        if HAS_QT:
            self.setWindowTitle("Village Citizen Registry - ASHA Offline Database")
            self.resize(850, 520)
            self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        title = QLabel("Select Village Resident for Assessment")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00E8C6;")
        layout.addWidget(title)

        # Search Input
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Type Name, Age, Phone, or ABHA (e.g., kishor, kamala, 50)...")
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_edit)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("NavBtn")
        clear_btn.clicked.connect(lambda: self.search_edit.clear())
        search_row.addWidget(clear_btn)
        layout.addLayout(search_row)

        # Table of Citizens
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Name", "Age / Group", "Gender", "Village", "Chronic Conditions", "ABHA ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows if hasattr(QTableWidget, "SelectRows") else 1)
        self.table.setSelectionMode(QTableWidget.SingleSelection if hasattr(QTableWidget, "SingleSelection") else 1)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        header = self.table.horizontalHeader()
        if hasattr(header, "setSectionResizeMode"):
            try:
                header.setSectionResizeMode(0, QHeaderView.ResizeToContents if hasattr(QHeaderView, "ResizeToContents") else 1)
                header.setSectionResizeMode(4, QHeaderView.Stretch if hasattr(QHeaderView, "Stretch") else 1)
            except Exception:
                pass
        layout.addWidget(self.table, stretch=1)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 13px;")
        btn_row.addWidget(self.status_lbl)
        btn_row.addStretch()

        select_btn = QPushButton("Select Citizen")
        select_btn.setObjectName("PrimaryBtn")
        select_btn.setMinimumHeight(48)
        select_btn.clicked.connect(self._on_select_clicked)
        btn_row.addWidget(select_btn)

        close_btn = QPushButton("Cancel")
        close_btn.setObjectName("NavBtn")
        close_btn.setMinimumHeight(48)
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # Initial Population
        self._populate_table(patient_registry.get_all())

    def _populate_table(self, patients: List[PatientRecord]):
        self.current_records = patients
        self.table.setRowCount(len(patients))
        for row, p in enumerate(patients):
            conds_str = ", ".join(p.chronic_conditions) if p.chronic_conditions else "None"
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.age_display_badge))
            self.table.setItem(row, 2, QTableWidgetItem(p.gender))
            self.table.setItem(row, 3, QTableWidgetItem(p.village))
            self.table.setItem(row, 4, QTableWidgetItem(conds_str))
            self.table.setItem(row, 5, QTableWidgetItem(p.abha_id))
        self.status_lbl.setText(f"Showing {len(patients)} citizen records")
        if patients:
            self.table.selectRow(0)

    def _on_search_text_changed(self, text: str):
        matches = patient_registry.search(text.strip())
        self._populate_table(matches)

    def _on_row_double_clicked(self, item):
        self._on_select_clicked()

    def _on_select_clicked(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        if 0 <= row < len(self.current_records):
            self.selected_patient = self.current_records[row]
            if self.on_selected:
                self.on_selected(self.selected_patient)
            self.accept()


class SpeechScreen(QWidget if HAS_QT else object):
    """
    Hands-free, touch-first speech consultation interface with ASHA village patient integration.
    """

    def __init__(self, retriever: HybridRetriever, parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.retriever = retriever
        self.audio_recorder = AudioRecorder(sample_rate=settings.AUDIO_SAMPLE_RATE)
        self.active_language = settings.DEFAULT_LANGUAGE
        self.thread_pool = QThreadPool.globalInstance() if HAS_QT else None
        self.last_result: Optional[Dict[str, Any]] = None
        self.on_patient_changed = None

        # Default to Kishor Kumar if present in registry, else first record
        default_list = patient_registry.search("kishor")
        self.active_patient: Optional[PatientRecord] = default_list[0] if default_list else (
            patient_registry.get_all()[0] if patient_registry.get_all() else None
        )
        self.active_vitals: Optional[Any] = None

        # 10-Second Click-to-Record State
        self.is_recording = False
        self.remaining_seconds = 10
        self.record_timer = QTimer(self) if HAS_QT else None
        if self.record_timer:
            self.record_timer.timeout.connect(self._on_record_tick)

        if HAS_QT:
            self._init_ui()

    def set_language(self, lang_code: str):
        """Updates active language from Language Selection screen."""
        self.active_language = lang_code
        if hasattr(self, "lang_badge"):
            lang_name = settings.SUPPORTED_LANGUAGES.get(lang_code, lang_code.upper())
            self.lang_badge.setText(f"Language: {lang_name}")

    def set_patient(self, patient: PatientRecord):
        """Updates active patient record from top navigation or search."""
        self.active_patient = patient
        if hasattr(self, "citizen_info_lbl"):
            self._update_citizen_display()
        if hasattr(self, "placeholder_label"):
            self.placeholder_label.setText(self._get_placeholder_text())

    def set_vitals(self, vitals: Any):
        """Updates active recorded vital signs."""
        self.active_vitals = vitals

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # 1. Header Info Row
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Speech Clinical Assistant")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.lang_badge = QLabel(f"Language: {self.active_language.upper()}")
        self.lang_badge.setStyleSheet("font-size: 14px; font-weight: 600; color: #1D4ED8; background: #EFF6FF; padding: 6px 12px; border-radius: 8px;")
        header_layout.addWidget(self.lang_badge)

        layout.addLayout(header_layout)

        # 2. Citizen Information Bar
        self.citizen_bar = QFrame()
        self.citizen_bar.setObjectName("CitizenBar")
        bar_layout = QHBoxLayout(self.citizen_bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)
        bar_layout.setSpacing(12)

        self.citizen_info_lbl = QLabel("")
        self.citizen_info_lbl.setObjectName("CitizenName")
        bar_layout.addWidget(self.citizen_info_lbl)

        bar_layout.addStretch()

        self.change_citizen_btn = QPushButton("🔍 Search / Change Citizen")
        self.change_citizen_btn.setObjectName("NavBtn")
        self.change_citizen_btn.setCursor(Qt.PointingHandCursor)
        self.change_citizen_btn.clicked.connect(self._open_citizen_search)
        bar_layout.addWidget(self.change_citizen_btn)

        layout.addWidget(self.citizen_bar)
        self._update_citizen_display()

        # 3. Emergency Warning Banner (Hidden by default)
        self.emergency_frame = QFrame()
        self.emergency_frame.setObjectName("EmergencyBanner")
        self.emergency_frame.setVisible(False)
        em_layout = QVBoxLayout(self.emergency_frame)
        self.emergency_label = QLabel("")
        self.emergency_label.setObjectName("EmergencyText")
        self.emergency_label.setWordWrap(True)
        em_layout.addWidget(self.emergency_label)
        layout.addWidget(self.emergency_frame)

        # 4. Main Scrollable Results Panel
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(12)

        # Welcome Placeholder
        self.placeholder_label = QLabel(self._get_placeholder_text())
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 17px; color: #64748B; padding: 30px; line-height: 1.5;")
        self.placeholder_label.setWordWrap(True)
        self.results_layout.addWidget(self.placeholder_label)

        self.scroll_area.setWidget(self.results_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # 5. Live Status & Indicator
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready to listen")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #2563EB;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.replay_btn = QPushButton("🔊 Replay Audio")
        self.replay_btn.setObjectName("NavBtn")
        self.replay_btn.setVisible(False)
        self.replay_btn.clicked.connect(self._replay_tts)
        status_layout.addWidget(self.replay_btn)

        layout.addLayout(status_layout)

        # 6. Click-to-Record Microphone Button Area (10s Auto-Send)
        mic_layout = QHBoxLayout()
        mic_layout.addStretch()

        self.mic_btn = QPushButton("🎤 Click to Speak (10s)")
        self.mic_btn.setObjectName("MicBtn")
        self.mic_btn.setMinimumSize(280, 74)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.clicked.connect(self._toggle_recording)
        mic_layout.addWidget(self.mic_btn)

        mic_layout.addStretch()
        layout.addLayout(mic_layout)

    def _get_placeholder_text(self) -> str:
        p_name = self.active_patient.name if self.active_patient else "Villager"
        return f"Ready for consultation ({p_name}). Click the microphone below, describe your symptoms, then click again or wait 10 seconds."

    def _update_citizen_display(self):
        if not self.active_patient:
            self.citizen_info_lbl.setText("👤 No Citizen Selected")
            return

        p = self.active_patient
        cond_text = f" &bull; {', '.join(p.chronic_conditions)}" if p.chronic_conditions else ""
        self.citizen_info_lbl.setText(
            f"👤 <b>{p.name}</b> ({p.age_display_badge}, {p.gender}) &bull; ABHA: {p.abha_id} &bull; {p.village}{cond_text}"
        )
        if self.on_patient_changed:
            self.on_patient_changed(f"{p.name} ({p.age_display_badge})")

    def _open_citizen_search(self):
        dialog = CitizenSearchDialog(parent=self, on_selected=self._on_citizen_selected)
        dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()

    def _on_citizen_selected(self, patient: PatientRecord):
        self.active_patient = patient
        self._update_citizen_display()
        self.placeholder_label.setText(self._get_placeholder_text())
        logger.info(f"Active citizen switched to: {patient.name} ({patient.age_display_badge})")

    def _toggle_recording(self):
        """1-click starts 10-second recording or sends early if clicked again."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_and_process()

    def _start_recording(self):
        """Starts audio recording with 10s live countdown."""
        self.is_recording = True
        self.remaining_seconds = 10
        self.emergency_frame.setVisible(False)
        self.mic_btn.setText("🛑 Stop & Send (10s)")
        self.mic_btn.setStyleSheet("background-color: #DC2626; color: white; border: 2px solid #F87171;")
        self.status_label.setText("Recording... Speak symptoms (10s auto-stop)")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444;")
        tts_service.stop_speaking()
        self.audio_recorder.start_recording()
        if self.record_timer:
            self.record_timer.start(1000)

    def _on_record_tick(self):
        """Ticks countdown every second and auto-sends at 0."""
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self._stop_and_process()
        else:
            self.mic_btn.setText(f"🛑 Stop & Send ({self.remaining_seconds}s)")
            self.status_label.setText(f"Recording... ({self.remaining_seconds}s left - click to send early)")

    def _stop_and_process(self):
        """Stops recording and immediately dispatches audio to AI pipeline."""
        if not self.is_recording:
            return
        if self.record_timer:
            self.record_timer.stop()
        self.is_recording = False
        self.mic_btn.setText("⏳ Processing...")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setStyleSheet("")
        self.status_label.setText("Understanding speech & searching clinical guidance...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F59E0B;")

        audio_data, wav_buf = self.audio_recorder.stop_recording()
        if len(audio_data) == 0:
            self.status_label.setText("No speech captured. Click to try again.")
            self.status_label.setStyleSheet("font-size: 16px; color: #94A3B8;")
            self.mic_btn.setText("🎤 Click to Speak (10s)")
            self.mic_btn.setEnabled(True)
            return

        patient_profile = self.active_patient.to_dict() if self.active_patient else {}
        if self.active_vitals:
            patient_profile["vitals"] = self.active_vitals.to_clinical_dict() if hasattr(self.active_vitals, "to_clinical_dict") else self.active_vitals

        # Launch pipeline worker on global thread pool
        worker = SpeechPipelineWorker(
            audio_data=wav_buf.getvalue(),
            language=self.active_language,
            retriever=self.retriever,
            patient_profile=patient_profile
        )
        worker.signals.status_changed.connect(self._update_status)
        worker.signals.emergency_alert.connect(self._show_emergency_alert)
        worker.signals.finished.connect(self._render_results)
        worker.signals.error.connect(self._handle_error)

        self._active_worker = worker
        if self.thread_pool:
            self.thread_pool.start(worker)

    @Slot(str)
    def _update_status(self, status: str):
        self.status_label.setText(status)
        if "Searching" in status or "Preparing" in status:
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
        elif "Speaking" in status:
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        elif "Ready" in status:
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00E8C6;")

    @Slot(str)
    def _show_emergency_alert(self, msg: str):
        self.emergency_label.setText(msg)
        self.emergency_frame.setVisible(True)

    @Slot(dict)
    def _render_results(self, res: Dict[str, Any]):
        self.last_result = res
        self.replay_btn.setVisible(True)
        self.placeholder_label.setVisible(False)

        # Clear existing result widgets
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # Localized Card Headers
        lbls = {
            "ta": {
                "query": "தெரிவிக்கப்பட்ட அறிகுறிகள் / கேள்வி",
                "guidance": "மருத்துவ வழிகாட்டுதல்",
                "actions": "பரிந்துரைக்கப்பட்ட அடுத்த படிகள்:",
                "warnings": "கவனிக்க வேண்டிய ஆபத்து அறிகுறிகள்:",
                "referral": "பரிந்துரை வழிகாட்டுதல்:"
            },
            "hi": {
                "query": "बताए गए लक्षण / प्रश्न",
                "guidance": "चिकित्सीय मार्गदर्शन",
                "actions": "सुझाए गए अगले कदम:",
                "warnings": "खतरे के लक्षण जिन पर ध्यान दें:",
                "referral": "रेफरल मार्गदर्शन:"
            },
            "gu": {
                "query": "જણાવેલ લક્ષણો / પ્રશ્ન",
                "guidance": "તબીબી માર્ગદર્શન",
                "actions": "ભલામણ કરેલ આગલા પગલાં:",
                "warnings": "ધ્યાન રાખવા જેવા જોખમી લક્ષણો:",
                "referral": "રેફરલ માર્ગદર્શન:"
            }
        }.get(self.active_language, {
            "query": "Reported Symptoms / Query",
            "guidance": "Clinical Guidance",
            "actions": "Recommended Next Steps:",
            "warnings": "Watch For Danger Signs:",
            "referral": "Referral Guidance:"
        })

        # Check if the query lacks clinical symptoms (greeting, unclear speech, or noise)
        if res.get("needs_retake"):
            retake_frame = QFrame()
            retake_frame.setObjectName("RetakeCard")
            r_layout = QVBoxLayout(retake_frame)
            r_layout.setSpacing(12)

            # Warning title
            r_title = QLabel(f"⚠️ {res.get('title', 'Clinical Symptoms Not Detected')}")
            r_title.setObjectName("RetakeTitle")
            r_title.setWordWrap(True)
            r_layout.addWidget(r_title)

            # Captured voice utterance
            captured_speech = res.get("query", "").strip()
            if captured_speech:
                c_lbl = QLabel(f"<b>{lbls['query']}:</b> \"{captured_speech}\"")
                c_lbl.setObjectName("RetakeCapturedText")
                c_lbl.setWordWrap(True)
                r_layout.addWidget(c_lbl)

            # Informative message and next step instructions
            r_body = QLabel(res.get("summary", ""))
            r_body.setObjectName("RetakeBody")
            r_body.setWordWrap(True)
            r_layout.addWidget(r_body)

            # Big prominent Retake Action Button
            btn_text = res.get("button_text", "🎤 மீண்டும் பேசவும் (Click to Retake)")
            retake_action_btn = QPushButton(btn_text)
            retake_action_btn.setObjectName("RetakeBtn")
            retake_action_btn.setCursor(Qt.PointingHandCursor)
            retake_action_btn.clicked.connect(self._start_recording)
            r_layout.addWidget(retake_action_btn)

            self.results_layout.addWidget(retake_frame)

            # Reset recording controls
            self.mic_btn.setText("🎤 Click to Speak (10s)")
            self.mic_btn.setEnabled(True)
            self.mic_btn.setStyleSheet("")
            return

        # 1. Query Card
        q_frame = QFrame()
        q_frame.setObjectName("CardFrame")
        q_layout = QVBoxLayout(q_frame)
        q_header = QLabel(lbls["query"])
        q_header.setObjectName("CardHeader")
        q_text = QLabel(res.get("query", ""))
        q_text.setObjectName("CardBody")
        q_text.setWordWrap(True)
        q_layout.addWidget(q_header)
        q_layout.addWidget(q_text)
        self.results_layout.addWidget(q_frame)

        # 1b. Recorded Patient Vital Signs Card (Hardware Sensors)
        vitals_dict = res.get("patient_profile", {}).get("vitals") or (
            self.active_vitals.to_clinical_dict() if (hasattr(self, "active_vitals") and self.active_vitals and hasattr(self.active_vitals, "to_clinical_dict")) else None
        )
        if vitals_dict:
            v_frame = QFrame()
            v_frame.setObjectName("CardFrame")
            v_frame.setStyleSheet("QFrame#CardFrame { border-left: 5px solid #0284C7; }")
            v_layout = QVBoxLayout(v_frame)
            v_layout.setContentsMargins(18, 14, 18, 14)
            v_layout.setSpacing(10)

            v_title = QLabel("📊 Recorded Patient Vital Signs (Jetson Hardware Sensors)")
            v_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0369A1;")
            v_layout.addWidget(v_title)

            metrics_row = QHBoxLayout()
            metrics_row.setSpacing(10)

            t_val = vitals_dict.get("temperature_f", 98.6)
            t_stat = vitals_dict.get("temperature_status", "Normal")
            t_chip = QLabel(f"🌡️ <b>Temp:</b> {t_val}°F ({t_stat})")
            t_chip.setStyleSheet("background: #F0F9FF; color: #0369A1; padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 600;")
            metrics_row.addWidget(t_chip)

            sp_val = vitals_dict.get("spo2_percent", 98)
            sp_stat = vitals_dict.get("spo2_status", "Normal")
            sp_chip = QLabel(f"💨 <b>SpO2:</b> {sp_val}% ({sp_stat})")
            sp_chip.setStyleSheet("background: #ECFDF5; color: #047857; padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 600;")
            metrics_row.addWidget(sp_chip)

            hr_val = vitals_dict.get("heart_rate_bpm", 74)
            hr_chip = QLabel(f"🫀 <b>Pulse:</b> {hr_val} BPM")
            hr_chip.setStyleSheet("background: #FEF2F2; color: #B91C1C; padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 600;")
            metrics_row.addWidget(hr_chip)

            ecg_stat = vitals_dict.get("ecg_status", "Normal Sinus")
            ecg_chip = QLabel(f"📈 <b>ECG:</b> {ecg_stat}")
            ecg_chip.setStyleSheet("background: #F5F3FF; color: #6D28D9; padding: 6px 12px; border-radius: 6px; font-size: 14px; font-weight: 600;")
            metrics_row.addWidget(ecg_chip)

            v_layout.addLayout(metrics_row)
            self.results_layout.addWidget(v_frame)

        # 2. Guidance Summary Card
        s_frame = QFrame()
        s_frame.setObjectName("CardFrame")
        s_layout = QVBoxLayout(s_frame)
        s_header = QLabel(lbls["guidance"])
        s_header.setObjectName("CardHeader")
        s_text = QLabel(res.get("summary", ""))
        s_text.setObjectName("CardBody")
        s_text.setWordWrap(True)
        s_layout.addWidget(s_header)
        s_layout.addWidget(s_text)

        # 2b. Age & Risk Personalization Alert Card (Highlighting 50+ or Pediatric Guidance)
        p = self.active_patient
        if p and (p.age >= 50 or p.age < 12 or p.chronic_conditions):
            lang = self.active_language.lower()
            age_frame = QFrame()
            age_frame.setObjectName("AgeGuidanceCard")
            age_layout = QVBoxLayout(age_frame)

            age_titles = {
                "ta": f"⚠️ வயது மற்றும் இடர் முன்னெச்சரிக்கைகள் ({p.age_display_badge})",
                "hi": f"⚠️ आयु और जोखिम संबंधी सावधानियां ({p.age_display_badge})",
                "gu": f"⚠️ ઉંમર અને જોખમ સંબંધિત સાવચેતી ({p.age_display_badge})",
                "en": f"⚠️ Age & Risk Factor Precautions ({p.age_display_badge})"
            }
            age_title = QLabel(age_titles.get(lang, age_titles["en"]))
            age_title.setObjectName("AgeGuidanceTitle")
            age_layout.addWidget(age_title)

            age_msg = ""
            if p.age >= 50:
                age_dict = {
                    "ta": f"நோயாளிக்கு {p.age} வயது (50+ வயதுடையவர்). இரத்த அழுத்தம் (BP) மற்றும் நாடித்துடிப்பை தினமும் இருமுறை கண்காணிக்கவும். பாராசிட்டமால் 2g/நாளுக்கு மேல் எடுக்க வேண்டாம். உயர் இரத்த அழுத்தம் இருந்தால் வலி நிவாரணி மாத்திரைகளைத் தவிர்க்கவும். காய்ச்சல் 48 மணி நேரத்திற்கு மேல் நீடித்தால் மருத்துவரை அணுகவும்.",
                    "hi": f"मरीज की उम्र {p.age} वर्ष (50+ वयस्क) है। दिन में दो बार ब्लड प्रेशर और नाड़ी की जांच करें। पेरासिटामोल 2 ग्राम/दिन से अधिक न लें और पेनकिलर से बचें। यदि बुखार 48 घंटे से अधिक रहे तो डॉक्टर को दिखाएं।",
                    "gu": f"દર્દીની ઉંમર {p.age} વર્ષ (50+ વયસ્ક) છે. દિવસમાં બે વાર બ્લડ પ્રેશર તપાસો. પેરાસિટામોલ દિવસમાં 2 ગ્રામથી વધુ ન લેવી. તાવ 48 કલાકથી વધુ રહે તો ડૉક્ટરની સલાહ લો.",
                    "en": f"Patient is {p.age} years old (Adult 50+). Monitor blood pressure and pulse twice daily. Ensure maximum daily Paracetamol does not exceed 2g/day and avoid NSAIDs if hypertensive. Seek medical evaluation if fever persists over 48 hours or causes confusion."
                }
                age_msg = age_dict.get(lang, age_dict["en"])
            elif p.age < 12:
                age_dict = {
                    "ta": f"குழந்தை நோயாளி ({p.age} வயது). பெரியவர்களுக்கான மாத்திரைகளை ஒருபோதும் கொடுக்க வேண்டாம். உடல் எடைக்கு ஏற்ற பாராசிட்டமால் சிரப் மட்டுமே பயன்படுத்தவும். ஆஸ்பிரின் மாத்திரை கண்டிப்பாகக் கூடாது. ஓ.ஆர்.எஸ் திரவம் அடிக்கடி கொடுக்கவும். குழந்தை உணவு உட்கொள்ள மறுத்தாலோ அல்லது வேகமாக மூச்சு விட்டாலோ உடனே மருத்துவமனைக்கு அழைத்துச் செல்லவும்.",
                    "hi": f"बाल रोगी ({p.age} वर्ष)। वयस्कों की गोलियां बिल्कुल न दें। केवल वजन अनुसार पेरासिटामोल सिरप दें। एस्पिरिन कभी न दें। बार-बार ओआरएस का घोल पिलाएं। यदि बच्चा दूध/खाना न ले या सांस तेज चले तो तुरंत अस्पताल ले जाएं।",
                    "gu": f"બાળ દર્દી ({p.age} વર્ષ). પુખ્ત વયના લોકોની ગોળીઓ ક્યારેય ન આપવી. માત્ર વજન મુજબ પેરાસિટામોલ સીરપ આપવી. એસ્પિરિન બિલકુલ ન આપવી. વારંવાર ORS આપવું. જો બાળક ખોરાક ન લે અથવા શ્વાસ ઝડપથી ચાલે તો તરત જ દવાખાને લઈ જવું.",
                    "en": f"Pediatric patient ({p.age} years). Strictly avoid adult tablets. Use weight-based Paracetamol syrup only. Never give Aspirin (Reye's syndrome risk). Give frequent sips of ORS. Urgent referral if child refuses feeds."
                }
                age_msg = age_dict.get(lang, age_dict["en"])

            if p.chronic_conditions:
                cond_hdr = {
                    "ta": "\nமுந்தைய நோய்கள்",
                    "hi": "\nपूर्व स्थितियां",
                    "gu": "\nપૂર્વ બીમારીઓ",
                    "en": "\nKnown Conditions"
                }.get(lang, "\nKnown Conditions")
                age_msg += f"{cond_hdr}: {', '.join(p.chronic_conditions)}"

            age_body = QLabel(age_msg)
            age_body.setObjectName("AgeGuidanceBody")
            age_body.setWordWrap(True)
            age_layout.addWidget(age_body)
            s_layout.addWidget(age_frame)

        # Recommended Actions
        actions = res.get("recommended_actions", [])
        if actions:
            act_header = QLabel(lbls["actions"])
            act_header.setStyleSheet("font-size: 16px; font-weight: 700; color: #1D4ED8; margin-top: 8px;")
            s_layout.addWidget(act_header)
            for act in actions:
                a_lbl = QLabel(f"• {act}")
                a_lbl.setWordWrap(True)
                a_lbl.setStyleSheet("color: #1E293B; font-size: 15px; line-height: 1.4;")
                s_layout.addWidget(a_lbl)

        # Warning Signs
        warnings = res.get("warning_signs", [])
        if warnings:
            w_header = QLabel(lbls["warnings"])
            w_header.setStyleSheet("font-size: 16px; font-weight: 700; color: #B45309; margin-top: 8px;")
            s_layout.addWidget(w_header)
            for w in warnings:
                w_lbl = QLabel(f"⚠️ {w}")
                w_lbl.setWordWrap(True)
                w_lbl.setStyleSheet("color: #92400E; font-size: 15px; font-weight: 600; line-height: 1.4;")
                s_layout.addWidget(w_lbl)

        # Referral Advice
        referral = res.get("referral", "")
        if referral:
            ref_lbl = QLabel(f"🏥 {lbls['referral']} {referral}")
            ref_lbl.setWordWrap(True)
            ref_lbl.setStyleSheet("color: #065F46; font-weight: 700; margin-top: 8px; font-size: 15px; background: #ECFDF5; padding: 8px 12px; border-radius: 8px;")
            s_layout.addWidget(ref_lbl)

        # Sources Citations
        sources = res.get("sources", [])
        if sources:
            src_str = " | ".join(sources)
            src_lbl = QLabel(f"Source: {src_str}")
            src_lbl.setObjectName("SourceCitation")
            src_lbl.setWordWrap(True)
            s_layout.addWidget(src_lbl)

        self.results_layout.addWidget(s_frame)

        # 3. Patient Details Card at the End of Summary
        if self.active_patient:
            pat_frame = QFrame()
            pat_frame.setObjectName("PatientSummaryCard")
            pat_layout = QVBoxLayout(pat_frame)
            pat_layout.setSpacing(6)

            p_head = QLabel("📋 Citizen Health Profile & Assessment Record")
            p_head.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8;")
            pat_layout.addWidget(p_head)

            p = self.active_patient
            c_text = ", ".join(p.chronic_conditions) if p.chronic_conditions else "None Reported"
            a_text = ", ".join(p.allergies) if p.allergies else "None Known"

            info_text = (
                f"<b>Name:</b> {p.name} &nbsp;&bull;&nbsp; "
                f"<b>Age/Gender:</b> {p.age}y ({p.gender}) &nbsp;&bull;&nbsp; "
                f"<b>ABHA ID:</b> {p.abha_id}<br>"
                f"<b>Village:</b> {p.village} &nbsp;&bull;&nbsp; "
                f"<b>Address:</b> {p.address} &nbsp;&bull;&nbsp; "
                f"<b>Contact:</b> {p.phone}<br>"
                f"<b>Pre-existing Conditions:</b> <span style='color: #F87171;'>{c_text}</span> &nbsp;&bull;&nbsp; "
                f"<b>Allergies:</b> {a_text}"
            )
            pat_info = QLabel(info_text)
            pat_info.setStyleSheet("color: #E2E8F0; font-size: 14px; line-height: 1.4;")
            pat_info.setWordWrap(True)
            pat_layout.addWidget(pat_info)
            self.results_layout.addWidget(pat_frame)

        # 4. Action Buttons (Print USB Slip & Start New Assessment)
        action_box = QFrame()
        action_layout = QHBoxLayout(action_box)
        action_layout.setSpacing(16)

        # USB Print Button
        print_btn = QPushButton("🖨️ Print Clinical Slip (USB)")
        print_btn.setObjectName("PrintBtn")
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.clicked.connect(self._print_report)
        action_layout.addWidget(print_btn)

        # Finish & Start New Assessment Button
        new_assess_btn = QPushButton("🔄 Finish & Start New Assessment")
        new_assess_btn.setObjectName("NewAssessmentBtn")
        new_assess_btn.setCursor(Qt.PointingHandCursor)
        new_assess_btn.clicked.connect(self._start_new_assessment)
        action_layout.addWidget(new_assess_btn)

        self.results_layout.addWidget(action_box)

        self.mic_btn.setText("🎤 Click to Speak (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")

    def _print_report(self):
        """Sends clinical slip directly to USB printer and archives PDF copy."""
        if not self.last_result:
            return
        patient_dict = self.active_patient.to_dict() if self.active_patient else {}
        if hasattr(self, "active_vitals") and self.active_vitals:
            patient_dict["vitals"] = self.active_vitals.to_clinical_dict() if hasattr(self.active_vitals, "to_clinical_dict") else self.active_vitals
        ok, msg = print_clinical_report(self, patient_dict, self.last_result, self.active_language)
        if ok:
            self.status_label.setText("Clinical slip dispatched to printer")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
            if HAS_QT and QMessageBox is not None:
                QMessageBox.information(self, "Clinical Assessment Printout", msg)

    def _start_new_assessment(self):
        """Cleans up current assessment state and prepares for next villager."""
        tts_service.stop_speaking()
        self.last_result = None
        self.replay_btn.setVisible(False)
        self.emergency_frame.setVisible(False)

        # Clear existing result cards
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        self.placeholder_label.setText(self._get_placeholder_text())
        self.placeholder_label.setVisible(True)
        self.status_label.setText("Ready to listen")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00E8C6;")
        self.mic_btn.setText("🎤 Click to Speak (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")
        logger.info("Assessment finished and reset for next citizen consultation.")

    def _replay_tts(self):
        """Re-synthesizes/plays the complete clinical guidance audio."""
        if self.last_result:
            spoken = self.last_result.get("spoken_text", self.last_result.get("summary", ""))
            tts_service.speak_async(spoken, language=self.active_language)

    @Slot(str)
    def _handle_error(self, err_msg: str):
        self.status_label.setText("Error processing request")
        self.status_label.setStyleSheet("font-size: 16px; color: #EF4444;")
        self.mic_btn.setText("🎤 Click to Speak (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")
        logger.error(f"Speech screen pipeline error: {err_msg}")
