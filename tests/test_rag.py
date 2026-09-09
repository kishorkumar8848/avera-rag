import pytest
import os
from pathlib import Path
from app.rag.schema import MedicalDocument
from app.rag.medline_ingest import MedlinePlusIngestor
from app.rag.protocol_ingest import IndianProtocolIngestor
from app.rag.hybrid_retriever import HybridRetriever
from app.safety.policies import ClinicalPolicyEngine
from app.core.config import settings


@pytest.fixture
def sample_documents():
    return [
        MedicalDocument(
            id="in_malaria_1",
            title="Malaria",
            aliases=["Plasmodium infection", "Chills fever"],
            summary="Intermittent high fever with chills. Give Paracetamol and ORS. Refer for RDT blood smear.",
            language="en",
            source="Indian_Protocol",
            authority="Ministry of Health and Family Welfare (MoHFW)",
            source_url="https://main.mohfw.gov.in",
            document_type="clinical_protocol"
        ),
        MedicalDocument(
            id="in_snakebite_1",
            title="Snake Bite",
            aliases=["Envenomation"],
            summary="Immobilize bitten limb with splint. Do NOT apply tourniquet. Transport urgently for Anti-Snake Venom (ASV).",
            language="en",
            source="Indian_Protocol",
            authority="Ministry of Health and Family Welfare (MoHFW)",
            source_url="https://main.mohfw.gov.in",
            document_type="clinical_protocol"
        ),
        MedicalDocument(
            id="mplus_diabetes_1",
            title="Diabetes",
            aliases=["Type 2 Diabetes", "High Blood Sugar"],
            summary="Diabetes is a disease in which blood glucose levels are above normal. A1C test measures 3-month average.",
            language="en",
            source="MedlinePlus",
            authority="National Library of Medicine (NIH)",
            source_url="https://medlineplus.gov/diabetes.html",
            document_type="health_education"
        )
    ]


def test_indian_protocol_ingestion():
    protocols_dir = settings.resolve_path(settings.INDIAN_PROTOCOLS_DIR)
    ingestor = IndianProtocolIngestor(str(protocols_dir))
    docs = ingestor.parse_all_protocols()
    assert len(docs) > 0
    titles = [d.title.lower() for d in docs]
    assert any("snake bite" in t or "malaria" in t or "leprosy" in t for t in titles)


def test_medlineplus_xml_parsing():
    xml_path = settings.resolve_path(settings.MEDLINEPLUS_XML_PATH)
    if not xml_path.exists():
        xml_path = settings.resolve_path("mplus_topics_2026-09-08.xml")
    assert xml_path.exists()

    ingestor = MedlinePlusIngestor(str(xml_path))
    # Test on whole_doc strategy
    docs = ingestor.parse_records(strategy="whole_doc")
    assert len(docs) > 0
    assert docs[0].language == "en"
    assert docs[0].source == "MedlinePlus"
    assert len(docs[0].summary) > 20


def test_hybrid_retriever_search(sample_documents, tmp_path):
    test_db = str(tmp_path / "test_rag.db")
    test_faiss = str(tmp_path / "test_faiss")

    retriever = HybridRetriever(db_path=test_db, faiss_dir=test_faiss)
    retriever.build_indexes(sample_documents)

    # Test BM25 keyword match for "malaria"
    results = retriever.retrieve("Patient shivering with chills and fever", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "Malaria" in top_result["title"] or "Snake" in top_result["title"]
    assert "citation" in top_result
    assert "MoHFW" in top_result["citation"]


def test_protocol_precedence_rule(sample_documents):
    retrieved = [
        {"title": "Diabetes Education", "source": "MedlinePlus"},
        {"title": "Snake Bite Protocol", "source": "Indian_Protocol"},
        {"title": "General Nutrition", "source": "MedlinePlus"}
    ]
    reordered = ClinicalPolicyEngine.enforce_protocol_precedence(retrieved)
    assert reordered[0]["source"] == "Indian_Protocol"
    assert reordered[0]["title"] == "Snake Bite Protocol"
