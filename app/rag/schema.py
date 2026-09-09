from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MedicalDocument(BaseModel):
    """
    Unified canonical record schema for MedlinePlus health topics
    and official Indian clinical protocols.
    """
    id: str = Field(description="Unique document or topic identifier.")
    title: str = Field(description="Primary clinical condition or topic title.")
    aliases: List[str] = Field(default_factory=list, description="Common medical aliases and also-called terms.")
    summary: str = Field(description="Cleaned, plain-text medical summary and guidelines.")
    language: str = Field(default="en", description="Language code (English primary).")
    source: str = Field(description="Source repository name (e.g. MedlinePlus or Indian_Protocol).")
    authority: str = Field(description="Official clinical authority (e.g. MoHFW, NLM, NHM).")
    source_url: str = Field(default="", description="Original source link or official document URL.")
    document_type: str = Field(default="clinical_protocol", description="Type: clinical_protocol or health_education.")
    version_date: Optional[str] = Field(default=None, description="Creation or update date metadata.")
    related_topics: List[str] = Field(default_factory=list, description="Associated disease groups or related topics.")

    def to_full_text(self) -> str:
        """Returns unified text representation for keyword and dense embedding indexing."""
        alias_str = f"Also known as: {', '.join(self.aliases)}. " if self.aliases else ""
        return f"Title: {self.title}\n{alias_str}Source: {self.authority} ({self.source})\n\n{self.summary}".strip()
