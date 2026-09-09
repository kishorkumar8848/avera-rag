import os
import re
import html
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.rag.schema import MedicalDocument
from app.core.logging import logger


def clean_html_tags(raw_html: str) -> str:
    """Unescapes HTML entities and strips XML/HTML tags, normalizing whitespace."""
    if not raw_html:
        return ""
    # Unescape HTML entities (&lt; &gt; &amp;)
    text = html.unescape(raw_html)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize multiple whitespace and newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def chunk_text_by_tokens(text: str, chunk_size: int = 400, chunk_overlap: int = 60) -> List[str]:
    """
    Splits text into overlapping token-like chunks (approximated by whitespace words).
    Benchmark Strategy B: 350–500 tokens with 50–80 token overlap.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start += chunk_size - chunk_overlap
    return chunks


class MedlinePlusIngestor:
    """
    Parses MedlinePlus Health Topics XML dataset into structured clinical education records.
    Filters for English subset and preserves key clinical metadata.
    """

    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)

    def parse_records(self, strategy: str = "whole_doc") -> List[MedicalDocument]:
        """
        Parses XML and returns MedicalDocument records.
        strategy:
            'whole_doc' -> Strategy A: One health topic = one retrieval document.
            'chunked'   -> Strategy B: 350-500 token chunks with 50-80 token overlap.
        """
        if not self.xml_path.exists():
            logger.error(f"MedlinePlus XML file not found at {self.xml_path}")
            return []

        logger.info(f"Parsing MedlinePlus XML from {self.xml_path}...")
        documents = []

        try:
            tree = ET.parse(str(self.xml_path))
            root = tree.getroot()

            for topic_elem in root.findall("health-topic"):
                language = topic_elem.attrib.get("language", "").strip()
                # Process only English records for primary corpus
                if language.lower() != "english":
                    continue

                topic_id = topic_elem.attrib.get("id", "")
                title = topic_elem.attrib.get("title", "").strip()
                source_url = topic_elem.attrib.get("url", "")
                date_created = topic_elem.attrib.get("date-created", "")
                meta_desc = topic_elem.attrib.get("meta-desc", "").strip()

                # Extract aliases (<also-called>)
                aliases = [
                    ac.text.strip() for ac in topic_elem.findall("also-called")
                    if ac.text and ac.text.strip()
                ]

                # Extract related topic groups (<group>)
                related_groups = [
                    grp.text.strip() for grp in topic_elem.findall("group")
                    if grp.text and grp.text.strip()
                ]

                # Extract and clean summary (<full-summary>)
                full_summary_elem = topic_elem.find("full-summary")
                summary_raw = full_summary_elem.text if full_summary_elem is not None and full_summary_elem.text else ""
                clean_summary = clean_html_tags(summary_raw)

                if not clean_summary and meta_desc:
                    clean_summary = meta_desc
                elif meta_desc and not clean_summary.startswith(meta_desc[:50]):
                    clean_summary = f"{meta_desc}\n\n{clean_summary}"

                if strategy == "whole_doc":
                    doc = MedicalDocument(
                        id=f"mplus_{topic_id}",
                        title=title,
                        aliases=aliases,
                        summary=clean_summary,
                        language="en",
                        source="MedlinePlus",
                        authority="National Library of Medicine (NIH)",
                        source_url=source_url,
                        document_type="health_education",
                        version_date=date_created,
                        related_topics=related_groups
                    )
                    documents.append(doc)
                else:
                    # Strategy B: chunked
                    chunks = chunk_text_by_tokens(clean_summary, chunk_size=400, chunk_overlap=60)
                    for idx, chunk_text in enumerate(chunks):
                        doc = MedicalDocument(
                            id=f"mplus_{topic_id}_chunk_{idx}",
                            title=f"{title} (Part {idx + 1})" if len(chunks) > 1 else title,
                            aliases=aliases,
                            summary=chunk_text,
                            language="en",
                            source="MedlinePlus",
                            authority="National Library of Medicine (NIH)",
                            source_url=source_url,
                            document_type="health_education",
                            version_date=date_created,
                            related_topics=related_groups
                        )
                        documents.append(doc)

            logger.info(f"MedlinePlus ingestion complete: {len(documents)} documents created (Strategy: {strategy}).")
            return documents

        except Exception as e:
            logger.error(f"Failed to parse MedlinePlus XML: {e}", exc_info=True)
            return []
