import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.config import settings

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LOGS_DIR = settings.resolve_path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
JSON_LOG_FILE = LOGS_DIR / "vyoma_telemetry.jsonl"
APP_LOG_FILE = LOGS_DIR / "vyoma_app.log"


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage()
        }
        if hasattr(record, "telemetry"):
            log_obj.update(record.telemetry)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logger(name: str = "vyoma") -> logging.Logger:
    """Configures console and file loggers with privacy filters."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    if not logger.handlers:
        # Console handler with clean human-readable output
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%H:%M:%S")
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
        
        # File handler (JSON Lines)
        f_handler = logging.FileHandler(JSON_LOG_FILE, encoding="utf-8")
        f_handler.setLevel(logging.DEBUG)
        f_handler.setFormatter(JsonFormatter())
        logger.addHandler(f_handler)

    return logger


logger = setup_logger("vyoma")


def log_interaction_telemetry(
    request_id: str,
    language: str,
    mode: str,
    latencies_ms: Dict[str, float],
    total_ms: float,
    status: str = "success",
    error_msg: Optional[str] = None
):
    """
    Logs structured interaction telemetry without any patient PII.
    Only metrics, language codes, and latencies are recorded.
    """
    telemetry_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "language": language,
        "mode": mode,
        "status": status,
        **latencies_ms,
        "total_ms": round(total_ms, 2)
    }
    if error_msg:
        telemetry_record["error"] = error_msg

    with open(JSON_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(telemetry_record, ensure_ascii=False) + "\n")

    # Check against latency budgets
    if "asr_ms" in latencies_ms and latencies_ms["asr_ms"] > settings.BUDGET_ASR_SEC * 1000:
        logger.warning(f"ASR latency exceeded budget: {latencies_ms['asr_ms']}ms > {settings.BUDGET_ASR_SEC * 1000}ms")
    if "qwen_ms" in latencies_ms and latencies_ms["qwen_ms"] > settings.BUDGET_LLM_SEC * 1000:
        logger.warning(f"Qwen latency exceeded budget: {latencies_ms['qwen_ms']}ms > {settings.BUDGET_LLM_SEC * 1000}ms")
    if total_ms > settings.BUDGET_TOTAL_SEC * 1000:
        logger.warning(f"Total interaction exceeded 15s budget: {total_ms}ms > {settings.BUDGET_TOTAL_SEC * 1000}ms")
