"""
Vyoma Offline Medical AI Assistant - ASHA Worker Village Patient Registry.
Provides offline local storage and search of village citizen demographics,
ABHA IDs, chronic conditions, and age categorization for clinical guidance tailoring.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

from app.core.config import settings
from app.core.logging import logger


@dataclass
class PatientRecord:
    id: str
    name: str
    age: int
    gender: str
    village: str
    address: str
    abha_id: str
    phone: str
    chronic_conditions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def age_category(self) -> str:
        """Categorizes patient for clinical protocol risk adjustments."""
        if self.age < 12:
            return "pediatric"
        elif self.age < 18:
            return "adolescent"
        elif self.age < 50:
            return "young_adult"
        elif self.age < 65:
            return "older_adult_50_plus"
        else:
            return "geriatric"

    @property
    def age_display_badge(self) -> str:
        """Returns concise UI badge text."""
        cat_map = {
            "pediatric": f"Pediatric ({self.age}y)",
            "adolescent": f"Adolescent ({self.age}y)",
            "young_adult": f"Adult ({self.age}y)",
            "older_adult_50_plus": f"Adult 50+ ({self.age}y)",
            "geriatric": f"Senior ({self.age}y)"
        }
        return cat_map.get(self.age_category, f"{self.age}y")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["age_category"] = self.age_category
        d["age_display_badge"] = self.age_display_badge
        return d


class PatientRegistry:
    """
    Offline Village Patient Registry manager.
    Loads and updates data/village_registry.json locally on device/Jetson.
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            self.file_path = Path(data_path)
        else:
            self.file_path = settings.resolve_path("data/village_registry.json")
        self._patients: List[PatientRecord] = []
        self.load()

    def load(self) -> None:
        """Loads records from JSON file."""
        if not self.file_path.exists():
            logger.warning(f"Village registry not found at {self.file_path}. Initializing empty.")
            self._patients = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            self._patients = [
                PatientRecord(
                    id=item.get("id", f"CITIZEN-{idx+1:03d}"),
                    name=item.get("name", "Unknown"),
                    age=int(item.get("age", 30)),
                    gender=item.get("gender", "Other"),
                    village=item.get("village", "Sundarapuram"),
                    address=item.get("address", ""),
                    abha_id=item.get("abha_id", ""),
                    phone=item.get("phone", ""),
                    chronic_conditions=item.get("chronic_conditions", []),
                    allergies=item.get("allergies", []),
                    notes=item.get("notes", "")
                )
                for idx, item in enumerate(raw_list)
            ]
            logger.info(f"Loaded {len(self._patients)} village citizen records from {self.file_path}.")
        except Exception as e:
            logger.error(f"Failed to load village registry: {e}")
            self._patients = []

    def save(self) -> None:
        """Persists records back to JSON file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([asdict(p) for p in self._patients], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self._patients)} patient records to {self.file_path}.")
        except Exception as e:
            logger.error(f"Failed to save village registry: {e}")

    def get_all(self) -> List[PatientRecord]:
        return list(self._patients)

    def get_by_id(self, patient_id: str) -> Optional[PatientRecord]:
        for p in self._patients:
            if p.id.lower() == patient_id.lower():
                return p
        return None

    def search(self, query: str, limit: int = 10) -> List[PatientRecord]:
        """
        Searches patients by name, phone, ABHA ID, village, or age.
        e.g. 'kishor', 'kamala', '50', '98401', 'sundarapuram'.
        """
        if not query or not query.strip():
            return self._patients[:limit]

        q = query.strip().lower()
        matches = []
        for p in self._patients:
            # Match score:
            # 1. Exact or prefix match on name (highest priority)
            name_lower = p.name.lower()
            if name_lower.startswith(q):
                matches.append((10, p))
            elif q in name_lower:
                matches.append((8, p))
            elif q == str(p.age):
                matches.append((7, p))
            elif q in p.phone.lower() or q in p.abha_id.lower().replace("-", ""):
                matches.append((6, p))
            elif q in p.village.lower() or q in p.address.lower():
                matches.append((4, p))
            elif any(q in c.lower() for c in p.chronic_conditions):
                matches.append((3, p))

        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in matches[:limit]]

    def register_patient(self, data: Dict[str, Any]) -> PatientRecord:
        """Registers a new village citizen offline and saves to file."""
        new_id = f"CITIZEN-{len(self._patients) + 1:03d}"
        rec = PatientRecord(
            id=data.get("id", new_id),
            name=data.get("name", "Unknown").strip(),
            age=int(data.get("age", 30)),
            gender=data.get("gender", "Female"),
            village=data.get("village", "Sundarapuram").strip(),
            address=data.get("address", "").strip(),
            abha_id=data.get("abha_id", "").strip(),
            phone=data.get("phone", "").strip(),
            chronic_conditions=data.get("chronic_conditions", []),
            allergies=data.get("allergies", []),
            notes=data.get("notes", "").strip()
        )
        self._patients.append(rec)
        self.save()
        return rec


# Global singleton instance
patient_registry = PatientRegistry()
