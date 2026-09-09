"""
Speech + Camera Screen for Vyoma Kiosk.
Provides camera preview, frame capture, Moondream structured observation extraction,
followed by voice symptom description and multimodal RAG reasoning.
"""

from typing import Optional, Dict, Any
from PIL import Image

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QImage, QPixmap, Qt, QThreadPool, QTimer, Slot, HAS_QT
)

from app.core.config import settings
from app.core.logging import logger
from app.hardware.camera import camera_service
from app.hardware.audio import AudioRecorder
from app.models.bhashini_tts import tts_service
from app.models.moondream_backend import moondream_backend
from app.ui.workers import MultimodalPipelineWorker
from app.rag.hybrid_retriever import HybridRetriever


class CameraScreen(QWidget if HAS_QT else object):
    """
    Multimodal consultation interface uniting visual inspection with voice symptoms.
    """

    def __init__(self, retriever: HybridRetriever, parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.retriever = retriever
        self.audio_recorder = AudioRecorder(sample_rate=settings.AUDIO_SAMPLE_RATE)
        self.active_language = settings.DEFAULT_LANGUAGE
        self.thread_pool = QThreadPool.globalInstance() if HAS_QT else None
        
        self.captured_image: Optional[Image.Image] = None
        self.visual_observations = []
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
        self.active_language = lang_code

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 14)
        main_layout.setSpacing(12)

        # Header Title
        header_layout = QHBoxLayout()
        title = QLabel("Multimodal Speech + Camera Assistant")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00E8C6;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Content Split: Left (Camera / Observations) & Right (Results / Guidance)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left Column: Camera Preview & Controls
        left_panel = QFrame()
        left_panel.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        self.preview_label = QLabel("Camera Preview Area")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #0B132B; border: 2px dashed #3A506B; border-radius: 8px; min-height: 200px;")
        left_layout.addWidget(self.preview_label)

        # Capture Button
        self.capture_btn = QPushButton("📸 Capture Photo")
        self.capture_btn.setObjectName("PrimaryBtn")
        self.capture_btn.clicked.connect(self._capture_photo)
        left_layout.addWidget(self.capture_btn)

        # Visual Observations Box
        self.obs_header = QLabel("Visual Observations (Moondream):")
        self.obs_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #38BDF8;")
        left_layout.addWidget(self.obs_header)

        self.obs_text = QLabel("No image captured yet.")
        self.obs_text.setWordWrap(True)
        self.obs_text.setStyleSheet("font-size: 14px; color: #CBD5E1;")
        left_layout.addWidget(self.obs_text)

        content_layout.addWidget(left_panel, stretch=1)

        # Right Column: Voice Input & Clinical Guidance Results
        right_panel = QFrame()
        right_panel.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        self.guidance_scroll = QScrollArea()
        self.guidance_scroll.setWidgetResizable(True)
        self.guidance_container = QWidget()
        self.guidance_layout = QVBoxLayout(self.guidance_container)

        self.guide_placeholder = QLabel("Capture a photo first, then hold the microphone below to describe additional symptoms.")
        self.guide_placeholder.setWordWrap(True)
        self.guide_placeholder.setAlignment(Qt.AlignCenter)
        self.guide_placeholder.setStyleSheet("font-size: 16px; color: #94A3B8; padding: 20px;")
        self.guidance_layout.addWidget(self.guide_placeholder)

        self.guidance_scroll.setWidget(self.guidance_container)
        right_layout.addWidget(self.guidance_scroll, stretch=1)

        # Status & Replay Bar
        status_bar = QHBoxLayout()
        self.status_label = QLabel("Step 1: Capture Photo")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #00E8C6;")
        status_bar.addWidget(self.status_label)
        status_bar.addStretch()

        self.replay_btn = QPushButton("🔊 Replay")
        self.replay_btn.setObjectName("NavBtn")
        self.replay_btn.setVisible(False)
        self.replay_btn.clicked.connect(self._replay_tts)
        status_bar.addWidget(self.replay_btn)

        right_layout.addLayout(status_bar)

        # Click-to-Record Button Area (10s Auto-Send)
        self.mic_btn = QPushButton("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setObjectName("MicBtn")
        self.mic_btn.setMinimumHeight(64)
        self.mic_btn.setEnabled(False)  # Enabled once photo is captured
        self.mic_btn.clicked.connect(self._toggle_recording)
        right_layout.addWidget(self.mic_btn)

        content_layout.addWidget(right_panel, stretch=1)

        main_layout.addLayout(content_layout)

    def _capture_photo(self):
        """Captures frame from camera and analyzes with Moondream."""
        self.status_label.setText("Capturing & analyzing...")
        success, pil_img, jpg_bytes = camera_service.capture_frame()

        if success and pil_img is not None:
            self.captured_image = pil_img
            # Render to Qt preview
            if jpg_bytes:
                qimg = QImage()
                qimg.loadFromData(jpg_bytes)
                pix = QPixmap.fromImage(qimg).scaled(
                    300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(pix)

            # Analyze with Moondream
            v_result = moondream_backend.analyze_image(self.captured_image)
            self.visual_observations = v_result.get("observations", [])
            obs_str = "\n".join(f"• {o}" for o in self.visual_observations)
            self.obs_text.setText(obs_str)

            self.status_label.setText("Step 2: Click mic to speak symptoms (10s)")
            self.mic_btn.setEnabled(True)
            self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
            self.mic_btn.setStyleSheet("border-color: #00E8C6; color: #00E8C6;")
        else:
            self.status_label.setText("Camera capture failed")

    def _toggle_recording(self):
        """1-click to start 10s recording or send early if clicked again."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_and_process()

    def _start_recording(self):
        self.is_recording = True
        self.remaining_seconds = 10
        self.mic_btn.setText("🛑 Stop & Send (10s)")
        self.mic_btn.setStyleSheet("background-color: #DC2626; color: white; border: 2px solid #F87171;")
        self.status_label.setText("Recording... Speak symptoms (10s auto-stop)")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #EF4444;")
        tts_service.stop_speaking()
        self.audio_recorder.start_recording()
        if self.record_timer:
            self.record_timer.start(1000)

    def _on_record_tick(self):
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self._stop_and_process()
        else:
            self.mic_btn.setText(f"🛑 Stop & Send ({self.remaining_seconds}s)")
            self.status_label.setText(f"Recording... ({self.remaining_seconds}s left - click to send early)")

    def _stop_and_process(self):
        if not self.is_recording:
            return
        if self.record_timer:
            self.record_timer.stop()
        self.is_recording = False
        self.mic_btn.setText("⏳ Processing...")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setStyleSheet("")
        self.status_label.setText("Processing multimodal clinical evidence...")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #F59E0B;")

        audio_data, wav_buf = self.audio_recorder.stop_recording()

        worker = MultimodalPipelineWorker(
            image=self.captured_image,
            speech_audio=wav_buf.getvalue() if len(audio_data) > 0 else None,
            text_query=None,
            language=self.active_language,
            retriever=self.retriever
        )
        worker.signals.status_changed.connect(self._update_status)
        worker.signals.finished.connect(self._render_results)
        worker.signals.error.connect(self._handle_error)

        self._active_worker = worker
        if self.thread_pool:
            self.thread_pool.start(worker)

    @Slot(str)
    def _update_status(self, status: str):
        self.status_label.setText(status)

    @Slot(dict)
    def _render_results(self, res: Dict[str, Any]):
        self.last_result = res
        self.replay_btn.setVisible(True)
        self.guide_placeholder.setVisible(False)

        while self.guidance_layout.count() > 1:
            item = self.guidance_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # Guidance Card
        frame = QFrame()
        frame.setObjectName("CardFrame")
        layout = QVBoxLayout(frame)

        header = QLabel("Grounded Clinical Guidance")
        header.setObjectName("CardHeader")
        layout.addWidget(header)

        body = QLabel(res.get("summary", ""))
        body.setObjectName("CardBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        actions = res.get("recommended_actions", [])
        if actions:
            act_header = QLabel("Recommended Action:")
            act_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #38BDF8; margin-top: 6px;")
            layout.addWidget(act_header)
            for act in actions:
                a_lbl = QLabel(f"• {act}")
                a_lbl.setWordWrap(True)
                layout.addWidget(a_lbl)

        referral = res.get("referral", "")
        if referral:
            r_lbl = QLabel(f"🏥 {referral}")
            r_lbl.setWordWrap(True)
            r_lbl.setStyleSheet("color: #A7F3D0; font-weight: bold; margin-top: 6px;")
            layout.addWidget(r_lbl)

        sources = res.get("sources", [])
        if sources:
            src_lbl = QLabel(f"Source: {' | '.join(sources)}")
            src_lbl.setObjectName("SourceCitation")
            src_lbl.setWordWrap(True)
            layout.addWidget(src_lbl)

        self.guidance_layout.addWidget(frame)
        self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("border-color: #00E8C6; color: #00E8C6;")

    def _replay_tts(self):
        if self.last_result:
            spoken = self.last_result.get("spoken_text", self.last_result.get("summary", ""))
            tts_service.speak_async(spoken, language=self.active_language)

    @Slot(str)
    def _handle_error(self, err_msg: str):
        self.status_label.setText("Error processing request")
        self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("border-color: #00E8C6; color: #00E8C6;")
        logger.error(f"Camera screen pipeline error: {err_msg}")
