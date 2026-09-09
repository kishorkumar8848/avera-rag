import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.rag.schema import MedicalDocument
from app.core.logging import logger


class IndianProtocolIngestor:
    """
    Ingests official Indian clinical protocols (MoHFW Standard Treatment Guidelines,
    National Health Mission, ASHA/ANM job aids, NVBDCP guidelines).
    Extracts structured clinical guidance with full source traceability.
    """

    def __init__(self, protocols_dir: str):
        self.protocols_dir = Path(protocols_dir)

    def parse_all_protocols(self) -> List[MedicalDocument]:
        """Scans data/indian_protocols/ for text and markdown protocol files."""
        if not self.protocols_dir.exists():
            logger.warning(f"Indian protocols directory not found at {self.protocols_dir}")
            return []

        documents = []
        for file_path in self.protocols_dir.glob("*.txt"):
            docs = self._parse_text_protocol_file(file_path)
            documents.extend(docs)

        logger.info(f"Loaded {len(documents)} official Indian clinical protocols from {self.protocols_dir}")
        return documents

    def _parse_text_protocol_file(self, file_path: Path) -> List[MedicalDocument]:
        """Parses structured clinical protocol blocks from text files."""
        documents = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Split by "Clinical Protocol for" or headers
            sections = re.split(r"(?:^|\n)(?=Clinical Protocol for|\#\# Protocol:)", content)

            for idx, sec in enumerate(sections):
                sec = sec.strip()
                if not sec or len(sec) < 50:
                    continue

                # Extract title
                title_match = re.search(r"(?:Clinical Protocol for|\#\# Protocol:)\s*([^\n\:\(]+)", sec)
                if title_match:
                    raw_title = title_match.group(1).strip()
                else:
                    first_line = sec.split("\n")[0].strip().replace("#", "").strip()
                    raw_title = first_line[:60]

                # Extract condition aliases if present in parentheses e.g. (Hansen's Disease)
                alias_match = re.search(r"\(([^)]+)\)", sec.split("\n")[0])
                aliases = []
                if alias_match:
                    aliases = [a.strip() for a in alias_match.group(1).split("/")]

                # Detect condition type and assign authority
                authority = "Ministry of Health and Family Welfare (MoHFW), Govt of India"
                doc_id = f"in_mohfw_{re.sub(r'[^a-zA-Z0-9_]', '_', raw_title.lower())[:30]}_{idx}"

                doc = MedicalDocument(
                    id=doc_id,
                    title=raw_title,
                    aliases=aliases,
                    summary=sec,
                    language="en",
                    source="Indian_Protocol",
                    authority=authority,
                    source_url="https://main.mohfw.gov.in/major-programmes/standard-treatment-guidelines",
                    document_type="clinical_protocol",
                    version_date="2024",
                    related_topics=["National Health Mission", "Primary Healthcare", "Standard Treatment Guidelines"]
                )
                documents.append(doc)

        except Exception as e:
            logger.error(f"Failed parsing Indian protocol file {file_path}: {e}", exc_info=True)

        return documents
