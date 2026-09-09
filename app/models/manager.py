import os
import gc
import threading
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.hardware.jetson_detector import JetsonDetector


class ModelManager:
    """
    Central coordinator for lazy model lifecycle, memory allocation,
    and unified RAM safety on NVIDIA Jetson Orin Nano (8GB limit).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.loaded_models: Dict[str, Any] = {}
        self._initialized = True
        logger.info("ModelManager initialized. Lazy loading active.")

    def memory_usage(self) -> Dict[str, float]:
        """Returns unified RAM statistics (total, available, used, percent)."""
        profile = JetsonDetector.get_system_profile()
        return {
            "ram_total_gb": profile.get("ram_total_gb") or 8.0,
            "ram_available_gb": profile.get("ram_available_gb") or 4.0,
            "ram_used_percent": profile.get("ram_used_percent") or 50.0
        }

    def check_memory_headroom(self, required_mb: float = 1200.0) -> bool:
        """
        Verifies if sufficient unified RAM exists before loading a model.
        If memory pressure is high, automatically unloads inactive models.
        """
        mem = self.memory_usage()
        used_pct = mem["ram_used_percent"]
        avail_mb = mem["ram_available_gb"] * 1024

        if used_pct >= settings.MAX_RAM_PERCENT or avail_mb < required_mb:
            logger.warning(
                f"Memory pressure detected: {used_pct}% used, {avail_mb:.1f}MB available. "
                f"Attempting to free memory before loading..."
            )
            if settings.AUTO_UNLOAD_MODELS:
                self.evict_inactive_models()

            # Recheck
            mem = self.memory_usage()
            if mem["ram_available_gb"] * 1024 < (required_mb * 0.7):
                logger.error(f"Cannot load model: RAM critically low ({mem['ram_available_gb']:.2f}GB free).")
                return False

        return True

    def register_model(self, name: str, instance: Any):
        """Registers an active model instance in the manager."""
        with self._lock:
            self.loaded_models[name] = instance
            logger.info(f"Model '{name}' registered in ModelManager. Active models: {list(self.loaded_models.keys())}")

    def is_loaded(self, name: str) -> bool:
        """Checks if a model is currently resident in memory."""
        with self._lock:
            return name in self.loaded_models

    def unload(self, name: str) -> bool:
        """Unloads a model from memory and forces garbage collection."""
        with self._lock:
            if name not in self.loaded_models:
                return False

            instance = self.loaded_models.pop(name)
            if hasattr(instance, "unload"):
                try:
                    instance.unload()
                except Exception as e:
                    logger.debug(f"Error calling unload() on {name}: {e}")

            del instance
            gc.collect()

            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

            logger.info(f"Model '{name}' successfully unloaded. Active models: {list(self.loaded_models.keys())}")
            return True

    def evict_inactive_models(self, keep: Optional[str] = None):
        """Evicts non-essential loaded models to reclaim RAM."""
        to_evict = [name for name in list(self.loaded_models.keys()) if name != keep]
        for name in to_evict:
            logger.info(f"Evicting inactive model '{name}' to preserve 8GB unified memory ceiling...")
            self.unload(name)

    def health_check(self) -> Dict[str, Any]:
        """Returns overall health and status of loaded models and memory."""
        mem = self.memory_usage()
        return {
            "loaded_models": list(self.loaded_models.keys()),
            "memory": mem,
            "status": "healthy" if mem["ram_used_percent"] < settings.MAX_RAM_PERCENT else "high_memory_warning"
        }


model_manager = ModelManager()
