"""
Speech Assistant Screen for Vyoma Kiosk.
Provides push-to-talk voice recording, dynamic status indicators,
structured guidance display, source citations, and non-blocking TTS audio replay.
"""

from typing import Optional, Dict, Any

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, Qt, QThreadPool, QTimer, Slot, HAS_QT
)

from app.core.config import settings
from app.core.logging import logger
from app.hardware.audio import AudioRecorder
from app.models.bhashini_tts import tts_service
from app.ui.workers import SpeechPipelineWorker
from app.rag.hybrid_retriever import HybridRetriever


class SpeechScreen(QWidget if HAS_QT else object):
    """
    Hands-free, touch-first speech consultation interface.
    """

    def __init__(self, retriever: HybridRetriever, parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.retriever = retriever
        self.audio_recorder = AudioRecorder(sample_rate=settings.AUDIO_SAMPLE_RATE)
        self.active_language = settings.DEFAULT_LANGUAGE
        self.thread_pool = QThreadPool.globalInstance() if HAS_QT else None
        self.last_result: Optional[Dict[str, Any]] = None

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

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        # Header Info Row
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Speech Clinical Assistant")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00E8C6;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.lang_badge = QLabel(f"Language: {self.active_language.upper()}")
        self.lang_badge.setStyleSheet("font-size: 14px; color: #94A3B8; background: #1C2541; padding: 4px 10px; border-radius: 6px;")
        header_layout.addWidget(self.lang_badge)

        layout.addLayout(header_layout)

        # Emergency Warning Banner (Hidden by default)
        self.emergency_frame = QFrame()
        self.emergency_frame.setObjectName("EmergencyBanner")
        self.emergency_frame.setVisible(False)
        em_layout = QVBoxLayout(self.emergency_frame)
        self.emergency_label = QLabel("")
        self.emergency_label.setObjectName("EmergencyText")
        self.emergency_label.setWordWrap(True)
        em_layout.addWidget(self.emergency_label)
        layout.addWidget(self.emergency_frame)

        # Main Scrollable Results Panel
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(12)

        # Welcome Placeholder
        self.placeholder_label = QLabel("Press and hold the microphone below, describe your symptoms, then release.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 18px; color: #94A3B8; padding: 30px;")
        self.results_layout.addWidget(self.placeholder_label)

        self.scroll_area.setWidget(self.results_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Live Status & Indicator
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready to listen")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00E8C6;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.replay_btn = QPushButton("🔊 Replay Audio")
        self.replay_btn.setObjectName("NavBtn")
        self.replay_btn.setVisible(False)
        self.replay_btn.clicked.connect(self._replay_tts)
        status_layout.addWidget(self.replay_btn)

        layout.addLayout(status_layout)

        # Click-to-Record Microphone Button Area (10s Auto-Send)
        mic_layout = QHBoxLayout()
        mic_layout.addStretch()

        self.mic_btn = QPushButton("🎤 Click to Speak (10s)")
        self.mic_btn.setObjectName("MicBtn")
        self.mic_btn.setMinimumSize(260, 72)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.clicked.connect(self._toggle_recording)
        mic_layout.addWidget(self.mic_btn)

        mic_layout.addStretch()
        layout.addLayout(mic_layout)

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

        # Launch pipeline worker on global thread pool
        worker = SpeechPipelineWorker(
            audio_data=wav_buf.getvalue(),
            language=self.active_language,
            retriever=self.retriever
        )
        worker.signals.status_changed.connect(self._update_status)
        worker.signals.emergency_alert.connect(self._show_emergency_alert)
        worker.signals.finished.connect(self._render_results)
        worker.signals.error.connect(self._handle_error)

        # Hold strong reference so Python GC does not delete C++ WorkerSignals while thread runs
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
            "te": {
                "query": "పేర్కొన్న లక్షణాలు / ప్రశ్న",
                "guidance": "వైద్య మార్గదర్శకత్వం",
                "actions": "సూచించిన తదుపరి చర్యలు:",
                "warnings": "ప్రమాద సంకేతాలు:",
                "referral": "సిఫార్సు మార్గదర్శకత్వం:"
            },
            "ml": {
                "query": "റിപ്പോർട്ട് ചെയ്ത ലക്ഷണങ്ങൾ / ചോദ്യം",
                "guidance": "ക്ലിനിക്കൽ മാർഗ്ഗനിർദ്ദേശം",
                "actions": "ശുപാർശ ചെയ്യുന്ന അടുത്ത ഘട്ടങ്ങൾ:",
                "warnings": "ശ്രദ്ധിക്കേണ്ട അപകട ലക്ഷണങ്ങൾ:",
                "referral": "റഫറൽ മാർഗ്ഗനിർദ്ദേശം:"
            },
            "kn": {
                "query": "ವರದಿ ಮಾಡಿದ ಲಕ್ಷಣಗಳು / ಪ್ರಶ್ನೆ",
                "guidance": "ವೈದ್ಯಕೀಯ ಮಾರ್ಗದರ್ಶನ",
                "actions": "ಶಿಫಾರಸು ಮಾಡಿದ ಮುಂದಿನ ಹಂತಗಳು:",
                "warnings": "ಅಪಾಯದ ಲಕ್ಷಣಗಳು:",
                "referral": "ರೆಫರಲ್ ಮಾರ್ಗದರ್ಶನ:"
            }
        }.get(self.active_language, {
            "query": "Reported Symptoms / Query",
            "guidance": "Clinical Guidance",
            "actions": "Recommended Next Steps:",
            "warnings": "Watch For Danger Signs:",
            "referral": "Referral Guidance:"
        })

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

        # Recommended Actions
        actions = res.get("recommended_actions", [])
        if actions:
            act_header = QLabel(lbls["actions"])
            act_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38BDF8; margin-top: 8px;")
            s_layout.addWidget(act_header)
            for act in actions:
                a_lbl = QLabel(f"• {act}")
                a_lbl.setWordWrap(True)
                a_lbl.setStyleSheet("color: #E2E8F0; font-size: 15px;")
                s_layout.addWidget(a_lbl)

        # Warning Signs
        warnings = res.get("warning_signs", [])
        if warnings:
            w_header = QLabel(lbls["warnings"])
            w_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #F59E0B; margin-top: 8px;")
            s_layout.addWidget(w_header)
            for w in warnings:
                w_lbl = QLabel(f"⚠️ {w}")
                w_lbl.setWordWrap(True)
                w_lbl.setStyleSheet("color: #FEF08A; font-size: 15px;")
                s_layout.addWidget(w_lbl)

        # Referral Advice
        referral = res.get("referral", "")
        if referral:
            ref_lbl = QLabel(f"🏥 {lbls['referral']} {referral}")
            ref_lbl.setWordWrap(True)
            ref_lbl.setStyleSheet("color: #A7F3D0; font-weight: bold; margin-top: 8px; font-size: 15px;")
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
        self.mic_btn.setText("🎤 Click to Speak (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")

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
