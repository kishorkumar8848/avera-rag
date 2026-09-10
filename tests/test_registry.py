import pytest
from app.safety.patient_registry import patient_registry, PatientRecord
from app.safety.clinical_protocols import lookup_clinical_protocol
from app.ui.report_printer import generate_report_html


def test_patient_registry_load():
    patients = patient_registry.get_all()
    assert len(patients) >= 10
    names = [p.name for p in patients]
    assert "Kishor Kumar" in names
    assert "Kamala Devi" in names


def test_patient_search():
    # 1. Search by name
    res_kishor = patient_registry.search("kishor")
    assert len(res_kishor) > 0
    assert res_kishor[0].name == "Kishor Kumar"
    assert res_kishor[0].age == 24
    assert res_kishor[0].village == "Sundarapuram"

    # 2. Search by age
    res_50 = patient_registry.search("50")
    assert len(res_50) > 0
    assert res_50[0].name == "Kamala Devi"
    assert res_50[0].age == 50
    assert any("Hypertension" in c for c in res_50[0].chronic_conditions)


def test_patient_age_categories():
    rec_ped = PatientRecord("1", "Child", 4, "Male", "V", "A", "ID", "123")
    assert rec_ped.age_category == "pediatric"
    assert "Pediatric" in rec_ped.age_display_badge

    rec_ado = PatientRecord("2", "Teen", 17, "Female", "V", "A", "ID", "123")
    assert rec_ado.age_category == "adolescent"

    rec_adult = PatientRecord("3", "Young", 24, "Male", "V", "A", "ID", "123")
    assert rec_adult.age_category == "young_adult"

    rec_50 = PatientRecord("4", "Middle", 50, "Female", "V", "A", "ID", "123")
    assert rec_50.age_category == "older_adult_50_plus"
    assert "Adult 50+" in rec_50.age_display_badge

    rec_senior = PatientRecord("5", "Elderly", 74, "Female", "V", "A", "ID", "123")
    assert rec_senior.age_category == "geriatric"


def test_age_tailored_guidance_for_50_year_old():
    # When ASHA worker consults for a 50-year-old with fever
    proto = lookup_clinical_protocol(
        query_text="severe fever and body pain",
        language="en",
        patient_age=50,
        patient_conditions=["Hypertension"]
    )
    assert proto is not None
    assert "age_guidance" in proto
    assert len(proto["age_guidance"]) > 0
    # Must advise blood pressure monitoring and paracetamol caution
    guidance_lower = proto["age_guidance"].lower()
    assert "blood pressure" in guidance_lower
    assert "paracetamol" in guidance_lower or "2g" in guidance_lower


def test_age_tailored_guidance_for_pediatric():
    # When ASHA worker consults for a 4-year-old child
    proto = lookup_clinical_protocol(
        query_text="fever and cough",
        language="en",
        patient_age=4
    )
    assert proto is not None
    guidance_lower = proto["age_guidance"].lower()
    assert "syrup" in guidance_lower or "pediatric" in guidance_lower
    assert "aspirin" in guidance_lower


def test_report_html_generation():
    patient_data = {
        "name": "Kishor Kumar",
        "age": 24,
        "gender": "Male",
        "village": "Sundarapuram",
        "address": "Plot 14, East Cross Street",
        "abha_id": "91-4432-8821-0012",
        "phone": "+91 98401 23456",
        "chronic_conditions": [],
        "allergies": []
    }
    clinical_result = {
        "query": "high fever and headache",
        "summary": "The patient presents with acute viral fever symptoms. Maintain bed rest and oral hydration.",
        "recommended_actions": ["Drink ORS fluids", "Tepid sponging if fever > 101F"],
        "warning_signs": ["Fever persisting beyond 3 days", "Convulsions"],
        "referral": "Sundarapuram Primary Health Centre",
        "sources": ["MoHFW Treatment Guidelines"]
    }
    html = generate_report_html(patient_data, clinical_result, language="en")
    assert "Kishor Kumar" in html
    assert "91-4432-8821-0012" in html
    assert "Sundarapuram" in html
    assert "National Health Mission" in html
    assert "Drink ORS fluids" in html
    assert "Sundarapuram Primary Health Centre" in html
