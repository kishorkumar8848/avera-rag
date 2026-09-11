"""
Speech + Camera Screen for AVERA Kiosk.
Provides live camera viewfinder preview, frame capture, Moondream visual observation extraction,
followed by voice symptom description, multimodal RAG reasoning, and USB slip printing.
"""

from typing import Optional, Dict, Any, List
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
from app.safety.patient_registry import patient_registry, PatientRecord
from app.ui.workers import MultimodalPipelineWorker
from app.rag.hybrid_retriever import HybridRetriever
from app.ui.report_printer import print_clinical_report


class CameraScreen(QWidget if HAS_QT else object):
    """
    Multimodal consultation interface uniting live visual inspection with voice symptoms.
    """

    def __init__(self, retriever: HybridRetriever, parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.retriever = retriever
        self.audio_recorder = AudioRecorder(sample_rate=settings.AUDIO_SAMPLE_RATE)
        self.active_language = settings.DEFAULT_LANGUAGE
        self.active_patient: Optional[PatientRecord] = patient_registry.get_patient("P001")
        self.thread_pool = QThreadPool.globalInstance() if HAS_QT else None

        self.captured_image: Optional[Image.Image] = None
        self.visual_observations = []
        self.last_result: Optional[Dict[str, Any]] = None

        # Viewfinder Live Stream Timer (~25 FPS)
        self.viewfinder_timer = QTimer(self) if HAS_QT else None
        if self.viewfinder_timer:
            self.viewfinder_timer.timeout.connect(self._update_viewfinder_frame)

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

    def set_patient(self, patient: PatientRecord):
        self.active_patient = patient
        if hasattr(self, "patient_meta_lbl"):
            self.patient_meta_lbl.setText(
                f"Active Patient: {patient.name}, {patient.age_display_badge} | Village: {patient.village} | ABHA: {patient.abha_id}"
            )

    def start_viewfinder(self):
        """Starts live camera viewfinder feed."""
        if self.viewfinder_timer and not self.viewfinder_timer.isActive() and self.captured_image is None:
            self.viewfinder_timer.start(40)

    def stop_viewfinder(self):
        """Halts live camera timer and releases camera hardware."""
        if self.viewfinder_timer and self.viewfinder_timer.isActive():
            self.viewfinder_timer.stop()
        camera_service.close()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_viewfinder()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_viewfinder()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(14)

        # Top Section: Screen Title & Patient Info Strip
        top_row = QHBoxLayout()
        title = QLabel("📷 Multimodal Visual Inspection & Voice Assistant")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.patient_meta_lbl = QLabel(
            f"Active Patient: {self.active_patient.name}, {self.active_patient.age_display_badge} | Village: {self.active_patient.village}"
            if self.active_patient else "No Patient Selected"
        )
        self.patient_meta_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #1D4ED8; background: #EFF6FF; padding: 6px 12px; border-radius: 8px;")
        top_row.addWidget(self.patient_meta_lbl)
        main_layout.addLayout(top_row)

        # Split Layout: Left (Camera & Observations) | Right (Voice & Guidance)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # ---------------- Left Panel: Camera Viewfinder & Controls ----------------
        left_panel = QFrame()
        left_panel.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        # Camera header row with hardware status badge
        cam_hdr_row = QHBoxLayout()
        preview_header = QLabel("Camera Live Viewfinder")
        preview_header.setStyleSheet("font-size: 16px; font-weight: 700; color: #1E293B;")
        cam_hdr_row.addWidget(preview_header)
        cam_hdr_row.addStretch()

        self.camera_status_badge = QLabel("🔍 Checking...")
        self.camera_status_badge.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 6px;")
        cam_hdr_row.addWidget(self.camera_status_badge)
        left_layout.addLayout(cam_hdr_row)

        # Viewfinder display label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(240)
        self.preview_label.setStyleSheet("background: #0F172A; border-radius: 12px; border: 2px solid #CBD5E1;")
        left_layout.addWidget(self.preview_label)

        # Capture / Retake Button
        self.capture_btn = QPushButton("📸 Capture Photo")
        self.capture_btn.setObjectName("PrimaryBtn")
        self.capture_btn.setMinimumHeight(56)
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.clicked.connect(self._toggle_photo_capture)
        left_layout.addWidget(self.capture_btn)

        # Visual Observations Box
        self.obs_header = QLabel("Visual Findings (Moondream Vision):")
        self.obs_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1D4ED8; margin-top: 4px;")
        left_layout.addWidget(self.obs_header)

        self.obs_text = QLabel("Live camera feed active. Aim at patient's skin rash, cut, or visible condition and click 'Capture Photo'.")
        self.obs_text.setWordWrap(True)
        self.obs_text.setStyleSheet("font-size: 14px; color: #475569; background: #F8FAFC; padding: 10px; border-radius: 8px; border: 1px solid #E2E8F0;")
        left_layout.addWidget(self.obs_text)

        content_layout.addWidget(left_panel, stretch=1)

        # ---------------- Right Panel: Speech Symptoms & Clinical Guidance ----------------
        right_panel = QFrame()
        right_panel.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        # Scrollable Guidance Container
        self.guidance_scroll = QScrollArea()
        self.guidance_scroll.setWidgetResizable(True)
        self.guidance_container = QWidget()
        self.guidance_layout = QVBoxLayout(self.guidance_container)
        self.guidance_layout.setContentsMargins(0, 0, 0, 0)
        self.guidance_layout.setSpacing(10)

        self.guide_placeholder = QLabel(
            "Step 1: Capture a photo of the visible condition using the left panel.\n"
            "Step 2: Hold or click the microphone button below to describe patient symptoms (duration, pain, fever)."
        )
        self.guide_placeholder.setWordWrap(True)
        self.guide_placeholder.setAlignment(Qt.AlignCenter)
        self.guide_placeholder.setStyleSheet("font-size: 15px; color: #64748B; padding: 30px; line-height: 1.5;")
        self.guidance_layout.addWidget(self.guide_placeholder)

        self.guidance_scroll.setWidget(self.guidance_container)
        right_layout.addWidget(self.guidance_scroll, stretch=1)

        # Status & Replay Bar
        status_bar = QHBoxLayout()
        self.status_label = QLabel("Step 1: Capture Photo")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #2563EB;")
        status_bar.addWidget(self.status_label)
        status_bar.addStretch()

        self.replay_btn = QPushButton("🔊 Listen Guidance")
        self.replay_btn.setObjectName("NavBtn")
        self.replay_btn.setVisible(False)
        self.replay_btn.setCursor(Qt.PointingHandCursor)
        self.replay_btn.clicked.connect(self._replay_tts)
        status_bar.addWidget(self.replay_btn)

        right_layout.addLayout(status_bar)

        # Click-to-Record Microphone Button
        self.mic_btn = QPushButton("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setObjectName("MicBtn")
        self.mic_btn.setMinimumHeight(64)
        self.mic_btn.setEnabled(False)  # Enabled once photo is captured
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.clicked.connect(self._toggle_recording)
        right_layout.addWidget(self.mic_btn)

        content_layout.addWidget(right_panel, stretch=1)

        main_layout.addLayout(content_layout, stretch=1)

    def _update_viewfinder_frame(self):
        """Pulls frame from live camera feed and renders onto Qt viewfinder label."""
        if self.captured_image is not None:
            return  # Preview is currently frozen on captured frame

        # Update hardware status indicator
        is_hw = camera_service.is_hardware_available
        if hasattr(self, "camera_status_badge"):
            if is_hw:
                self.camera_status_badge.setText("🟢 Live USB Camera Active")
                self.camera_status_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #065F46; background: #D1FAE5; padding: 4px 8px; border-radius: 6px;")
            else:
                self.camera_status_badge.setText("🟡 Camera Disconnected")
                self.camera_status_badge.setStyleSheet("font-size: 12px; font-weight: 700; color: #92400E; background: #FEF3C7; padding: 4px 8px; border-radius: 6px;")

        success, pil_img, jpg_bytes = camera_service.capture_frame()
        if success and jpg_bytes:
            qimg = QImage()
            qimg.loadFromData(jpg_bytes)
            lbl_w = max(self.preview_label.width(), 340)
            lbl_h = max(self.preview_label.height(), 240)
            pix = QPixmap.fromImage(qimg).scaled(
                lbl_w, lbl_h,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(pix)

    def _toggle_photo_capture(self):
        """Handles Capture Photo or Retake Photo toggle."""
        if self.captured_image is None:
            # Capture photo
            self.status_label.setText("Capturing & analyzing photo...")
            success, pil_img, jpg_bytes = camera_service.capture_frame()
            if success and pil_img is not None:
                self.captured_image = pil_img
                # Stop live preview loop while image is inspected
                if self.viewfinder_timer:
                    self.viewfinder_timer.stop()

                if jpg_bytes:
                    qimg = QImage()
                    qimg.loadFromData(jpg_bytes)
                    pix = QPixmap.fromImage(qimg).scaled(
                        self.preview_label.width() or 340, 240,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(pix)

                # Extract visual observations via Moondream
                v_result = moondream_backend.analyze_image(self.captured_image)
                self.visual_observations = v_result.get("observations", [])
                obs_str = "\n".join(f"• {o}" for o in self.visual_observations)
                self.obs_text.setText(obs_str)

                self.capture_btn.setText("🔄 Retake Photo")
                self.capture_btn.setObjectName("NavBtn")
                self.capture_btn.style().unpolish(self.capture_btn)
                self.capture_btn.style().polish(self.capture_btn)

                self.status_label.setText("Step 2: Click microphone to speak symptoms (10s)")
                self.mic_btn.setEnabled(True)
            else:
                self.status_label.setText("Capture failed. Try again.")
        else:
            # Retake photo
            self.captured_image = None
            self.visual_observations = []
            self.obs_text.setText("Live camera feed active. Aim at patient's condition and click 'Capture Photo'.")
            self.capture_btn.setText("📸 Capture Photo")
            self.capture_btn.setObjectName("PrimaryBtn")
            self.capture_btn.style().unpolish(self.capture_btn)
            self.capture_btn.style().polish(self.capture_btn)
            self.status_label.setText("Step 1: Capture Photo")
            self.mic_btn.setEnabled(False)
            self.start_viewfinder()

    def _toggle_recording(self):
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_and_process()

    def _start_recording(self):
        self.is_recording = True
        self.remaining_seconds = 10
        self.mic_btn.setText("🛑 Stop & Send (10s)")
        self.mic_btn.setStyleSheet("background-color: #DC2626; color: white; border: 2px solid #EF4444;")
        self.status_label.setText("Listening... Speak patient symptoms (10s auto-stop)")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #DC2626;")
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
            self.status_label.setText(f"Listening... ({self.remaining_seconds}s left)")

    def _stop_and_process(self):
        if not self.is_recording:
            return
        if self.record_timer:
            self.record_timer.stop()
        self.is_recording = False
        self.mic_btn.setText("⏳ Processing Guidance...")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setStyleSheet("")
        self.status_label.setText("Analyzing visual features & clinical evidence...")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #D97706;")

        audio_data, wav_buf = self.audio_recorder.stop_recording()

        worker = MultimodalPipelineWorker(
            image=self.captured_image,
            speech_audio=wav_buf.getvalue() if len(audio_data) > 0 else None,
            text_query=None,
            language=self.active_language,
            retriever=self.retriever,
            patient_profile=self.active_patient.to_dict() if self.active_patient else None
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

        # Clear previous guidance items
        while self.guidance_layout.count() > 1:
            item = self.guidance_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # 1. Main Guidance Card
        frame = QFrame()
        frame.setObjectName("CardFrame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        header = QLabel("Grounded Clinical Guidance")
        header.setObjectName("CardHeader")
        layout.addWidget(header)

        body = QLabel(res.get("summary", ""))
        body.setObjectName("CardBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        actions = res.get("recommended_actions", [])
        if actions:
            act_header = QLabel("Recommended Non-Pharmacological Care:")
            act_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #1D4ED8; margin-top: 6px;")
            layout.addWidget(act_header)
            for act in actions:
                a_lbl = QLabel(f"• {act}")
                a_lbl.setWordWrap(True)
                a_lbl.setStyleSheet("font-size: 15px; color: #1E293B;")
                layout.addWidget(a_lbl)

        referral = res.get("referral", "")
        if referral:
            r_lbl = QLabel(f"🏥 Referral: {referral}")
            r_lbl.setWordWrap(True)
            r_lbl.setStyleSheet("color: #047857; font-weight: 700; font-size: 15px; margin-top: 6px; background: #ECFDF5; padding: 8px 12px; border-radius: 8px;")
            layout.addWidget(r_lbl)

        sources = res.get("sources", [])
        if sources:
            src_lbl = QLabel(f"Source: {' | '.join(sources)}")
            src_lbl.setObjectName("SourceCitation")
            src_lbl.setWordWrap(True)
            layout.addWidget(src_lbl)

        self.guidance_layout.addWidget(frame)

        # 2. Age-Tailored Guidance Card (If applicable)
        if self.active_patient and (self.active_patient.age >= 50 or self.active_patient.age < 12):
            age_card = QFrame()
            age_card.setObjectName("AgeGuidanceCard")
            age_layout = QVBoxLayout(age_card)
            age_layout.setSpacing(6)

            if self.active_patient.age >= 50:
                a_title = QLabel(f"⚠️ Older Adult Care Protocol (Age {self.active_patient.age}y)")
                a_body = QLabel(
                    f"Patient is {self.active_patient.age} years old. Monitor blood pressure and pulse twice daily. "
                    "Keep Paracetamol within 2g/day max and avoid NSAIDs like Ibuprofen if hypertensive."
                )
            else:
                a_title = QLabel(f"👶 Pediatric Care Protocol (Age {self.active_patient.age}y)")
                a_body = QLabel(
                    f"Patient is a child ({self.active_patient.age}y). Avoid adult tablets; use weight-based Paracetamol syrup only. "
                    "Never administer Aspirin. Provide frequent sips of ORS."
                )

            a_title.setObjectName("AgeGuidanceTitle")
            a_body.setObjectName("AgeGuidanceBody")
            a_body.setWordWrap(True)
            age_layout.addWidget(a_title)
            age_layout.addWidget(a_body)
            self.guidance_layout.addWidget(age_card)

        # 3. Patient Demographics Summary Card
        if self.active_patient:
            demo_card = QFrame()
            demo_card.setObjectName("PatientSummaryCard")
            demo_layout = QVBoxLayout(demo_card)
            demo_layout.setSpacing(6)

            d_title = QLabel(f"👤 Patient Record: {self.active_patient.name}")
            d_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
            demo_layout.addWidget(d_title)

            meta_txt = (
                f"Age: {self.active_patient.age}y | Gender: {self.active_patient.gender} | "
                f"Village: {self.active_patient.village} | Address: {self.active_patient.address}\n"
                f"ABHA ID: {self.active_patient.abha_id} | Phone: {self.active_patient.phone}\n"
                f"Chronic Conditions: {', '.join(self.active_patient.chronic_conditions) if self.active_patient.chronic_conditions else 'None reported'}"
            )
            meta_lbl = QLabel(meta_txt)
            meta_lbl.setWordWrap(True)
            meta_lbl.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.4;")
            demo_layout.addWidget(meta_lbl)
            self.guidance_layout.addWidget(demo_card)

        # 4. Action Buttons: Print Slip & Finish Assessment
        btn_box = QWidget()
        btn_layout = QHBoxLayout(btn_box)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(14)

        print_btn = QPushButton("🖨️ Print Clinical Slip (USB)")
        print_btn.setObjectName("PrintBtn")
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.clicked.connect(self._print_clinical_slip)
        btn_layout.addWidget(print_btn)

        new_btn = QPushButton("🔄 Finish & New Assessment")
        new_btn.setObjectName("NewAssessmentBtn")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._finish_and_reset_assessment)
        btn_layout.addWidget(new_btn)

        self.guidance_layout.addWidget(btn_box)

        # Reset mic button
        self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")
        self.status_label.setText("Ready")

    def _print_clinical_slip(self):
        """Sends clinical assessment slip to USB printer or saves offline PDF."""
        if not self.last_result:
            return
        p_data = self.active_patient.to_dict() if self.active_patient else {
            "name": "General Resident", "age": 30, "gender": "Unknown", "village": "Sundarapuram"
        }
        print_clinical_report(
            parent_widget=self,
            patient_data=p_data,
            clinical_result=self.last_result,
            language=self.active_language
        )

    def _finish_and_reset_assessment(self):
        """Cleans up audio, unfreezes viewfinder, and readies kiosk for next villager."""
        tts_service.stop_speaking()
        self.last_result = None
        self.captured_image = None
        self.visual_observations = []
        self.replay_btn.setVisible(False)

        while self.guidance_layout.count() > 1:
            item = self.guidance_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        self.guide_placeholder.setVisible(True)
        self.obs_text.setText("Live camera feed active. Aim at patient's condition and click 'Capture Photo'.")
        self.capture_btn.setText("📸 Capture Photo")
        self.capture_btn.setObjectName("PrimaryBtn")
        self.capture_btn.style().unpolish(self.capture_btn)
        self.capture_btn.style().polish(self.capture_btn)

        self.status_label.setText("Step 1: Capture Photo")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #2563EB;")
        self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setStyleSheet("")
        self.start_viewfinder()
        logger.info("Camera assessment finished and reset for next citizen consultation.")

    def _replay_tts(self):
        if self.last_result:
            spoken = self.last_result.get("spoken_text", self.last_result.get("summary", ""))
            tts_service.speak_async(spoken, language=self.active_language)

    @Slot(str)
    def _handle_error(self, err_msg: str):
        self.status_label.setText("Error processing request")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #DC2626;")
        self.mic_btn.setText("🎤 Click to Speak Symptoms (10s)")
        self.mic_btn.setEnabled(True)
        self.mic_btn.setStyleSheet("")
        logger.error(f"Camera screen pipeline error: {err_msg}")
