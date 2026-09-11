import os
from pathlib import Path
from typing import List, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Application & Environment
    PROJECT_NAME: str = "AVERA - Medical AI Assistant"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # Display & Kiosk (Waveshare 7-inch 1024x600)
    UI_WIDTH: int = 1024
    UI_HEIGHT: int = 600
    FULLSCREEN: bool = False  # Set to True on Jetson kiosk autostart

    # Supported Languages
    SUPPORTED_LANGUAGES: Dict[str, str] = {
        "en": "English",
        "hi": "हिन्दी (Hindi)",
        "ta": "தமிழ் (Tamil)",
        "te": "తెలుగు (Telugu)",
        "kn": "ಕನ್ನಡ (Kannada)",
        "ml": "മലയാളം (Malayalam)",
        "bn": "বাংলা (Bengali)",
        "mr": "मराठी (Marathi)",
        "gu": "ગુજરાતી (Gujarati)",
        "pa": "ਪੰਜਾਬੀ (Punjabi)"
    }
    DEFAULT_LANGUAGE: str = "en"

    # Audio Hardware (Jetson Orin Nano)
    AUDIO_INPUT_DEVICE: str = "plughw:1,0"
    AUDIO_OUTPUT_DEVICE: str = "plughw:0,0"
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    VAD_ENERGY_THRESHOLD: float = 0.015
    VAD_SILENCE_DURATION: float = 1.2

    # Camera
    CAMERA_INDEX: int = 0
    CAMERA_BACKEND: str = "opencv"
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480

    # LLM Settings (Qwen2.5-1.5B-Instruct)
    LLM_BACKEND: str = "llama_cpp"  # llama_cpp or ollama
    LLM_MODEL_PATH: str = "models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    LLM_TEMPERATURE: float = 0.15
    LLM_TOP_P: float = 0.85
    LLM_MAX_NEW_TOKENS: int = 512
    LLM_N_CTX: int = 2048
    LLM_N_GPU_LAYERS: int = 28
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    # Vision Model (Moondream 0.5B INT4)
    MOONDREAM_MODEL_PATH: str = "models/moondream-0_5b-int4"
    MOONDREAM_MAX_TOKENS: int = 100

    # Speech Services (Bhashini Local)
    BHASHINI_MODELS_DIR: str = "models/bhashini"
    BHASHINI_ASR_URL: str = "http://localhost:8001/asr"
    BHASHINI_NMT_URL: str = "http://localhost:8002/nmt"
    BHASHINI_TTS_URL: str = "http://localhost:8003/tts"
    ASR_PROVIDER: str = "bhashini"
    TTS_PROVIDER: str = "bhashini"

    # RAG & Knowledge Base
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    MEDLINEPLUS_XML_PATH: str = "data/medlineplus/mplus_topics.xml"
    INDIAN_PROTOCOLS_DIR: str = "data/indian_protocols"
    SQLITE_DB_PATH: str = "indexes/medical_kb.db"
    FAISS_INDEX_DIR: str = "indexes/faiss"
    TOP_K_RETRIEVAL: int = 5
    TOP_K_CONTEXT: int = 4

    # Latency Budgets (seconds)
    BUDGET_ASR_SEC: float = 3.0
    BUDGET_NMT_SEC: float = 1.0
    BUDGET_RAG_SEC: float = 0.5
    BUDGET_VISION_SEC: float = 3.0
    BUDGET_LLM_SEC: float = 4.0
    BUDGET_TTS_SEC: float = 2.0
    BUDGET_TOTAL_SEC: float = 15.0

    # Memory Safety (8GB Unified RAM Limits)
    MAX_RAM_PERCENT: float = 85.0
    WARN_RAM_PERCENT: float = 75.0
    AUTO_UNLOAD_MODELS: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(ROOT_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def resolve_path(self, relative_path: str) -> Path:
        """Resolves a relative path against the project root."""
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return (ROOT_DIR / p).resolve()


settings = Settings()
