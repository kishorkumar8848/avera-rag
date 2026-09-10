"""
Vyoma Offline Medical AI Assistant - Direct USB Printer & Clinical Slip Generator.
Formats and prints official National Health Mission (NHM) / ASHA village consultation records
directly to connected USB printers (thermal roll or standard page) with automatic offline PDF backup.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.ui.qt_compat import (
    QTextDocument, QPrinter, QPrintDialog, QPrinterInfo,
    QMessageBox, QWidget, HAS_QT
)


def get_available_printers() -> List[Tuple[str, bool]]:
    """
    Returns list of (printer_name, is_default) available on the host system.
    Identifies USB-connected printers.
    """
    if not HAS_QT or QPrinterInfo is None:
        return []

    try:
        printers = QPrinterInfo.availablePrinters()
        default_name = QPrinterInfo.defaultPrinterName()
        result = []
        for p in printers:
            name = p.printerName()
            is_def = (name == default_name)
            result.append((name, is_def))
        return result
    except Exception as e:
        logger.warning(f"Error querying system printers: {e}")
        return []


def is_virtual_printer(name: str) -> bool:
    """Checks whether printer is a virtual file exporter rather than physical hardware."""
    nl = name.lower()
    return any(v in nl for v in ["pdf", "xps", "onenote", "fax", "document writer", "print to file"])


def find_usb_printer() -> Optional[str]:
    """
    Scans system printers for an attached physical USB printer or valid hardware printer.
    Excludes virtual printers (PDF, XPS, Fax).
    """
    printers = get_available_printers()
    if not printers:
        return None

    # 1. Look for explicit 'usb' or POS/thermal keywords
    for name, _ in printers:
        nl = name.lower()
        if not is_virtual_printer(name):
            if any(k in nl for k in ["usb", "pos", "thermal", "receipt", "epson", "tvs", "zebra", "citizen", "tsc"]):
                logger.info(f"Found USB / POS hardware printer: '{name}'")
                return name

    # 2. Return non-virtual default hardware printer
    for name, is_def in printers:
        if is_def and not is_virtual_printer(name):
            logger.info(f"Using default hardware printer: '{name}'")
            return name

    # 3. Return first non-virtual printer
    for name, _ in printers:
        if not is_virtual_printer(name):
            return name

    return None



def generate_report_html(
    patient_data: Optional[Dict[str, Any]],
    clinical_result: Dict[str, Any],
    language: str = "en"
) -> str:
    """
    Builds a clean, high-contrast, official MoHFW / NHM clinical assessment slip.
    Optimized for both standard A4/A5 printers and 80mm USB thermal roll printers.
    """
    now_str = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    p = patient_data or {}
    p_name = p.get("name", "Unknown Citizen")
    p_age = p.get("age", "--")
    p_gender = p.get("gender", "--")
    p_village = p.get("village", "Sundarapuram")
    p_address = p.get("address", "--")
    p_abha = p.get("abha_id", "Not Assigned")
    p_phone = p.get("phone", "--")
    p_conds = ", ".join(p.get("chronic_conditions", [])) or "None Reported"
    p_allergies = ", ".join(p.get("allergies", [])) or "None Known"

    query_text = clinical_result.get("query", "--")
    summary = clinical_result.get("summary", "")
    actions = clinical_result.get("recommended_actions", [])
    warnings = clinical_result.get("warning_signs", [])
    referral = clinical_result.get("referral", "Primary Health Centre (PHC)")
    sources = " | ".join(clinical_result.get("sources", ["MoHFW Standard Treatment Guidelines"]))
    is_emergency = clinical_result.get("is_emergency", False)

    # Emergency highlight badge
    triage_badge = (
        "<div style='background-color: #DC2626; color: white; padding: 6px 12px; font-weight: bold; font-size: 14px; text-align: center; border-radius: 4px; margin-bottom: 8px;'>"
        "🚨 URGENT EMERGENCY - IMMEDIATE RED FLAG MEDICAL ESCALATION REQUIRED 🚨</div>"
        if is_emergency else
        "<div style='background-color: #059669; color: white; padding: 4px 10px; font-weight: bold; font-size: 12px; text-align: center; border-radius: 4px; margin-bottom: 8px;'>"
        "✅ COMMUNITY HEALTH TRIAGE - NON-EMERGENCY HOME CARE & MONITORING</div>"
    )

    # Actions list items
    actions_html = "".join(f"<li style='margin-bottom: 4px;'>{act}</li>" for act in actions) if actions else "<li>Standard symptomatic rest and hydration.</li>"
    warnings_html = "".join(f"<li style='margin-bottom: 4px; color: #B91C1C;'><b>⚠️ {w}</b></li>" for w in warnings) if warnings else "<li>Fever persisting over 3 days or sudden severe pain.</li>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            color: #1E293B;
            line-height: 1.4;
            padding: 10px;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 8px;
            margin-bottom: 10px;
        }}
        .title {{
            font-size: 16px;
            font-weight: bold;
            color: #0F172A;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .subtitle {{
            font-size: 11px;
            color: #475569;
            font-weight: 600;
        }}
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
        }}
        .meta-table td {{
            padding: 5px 8px;
            font-size: 11px;
            border-bottom: 1px solid #E2E8F0;
        }}
        .meta-label {{
            font-weight: bold;
            color: #334155;
            width: 25%;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: bold;
            color: #0F766E;
            border-bottom: 1px solid #99F6E4;
            padding-bottom: 3px;
            margin-top: 10px;
            margin-bottom: 6px;
            text-transform: uppercase;
        }}
        .summary-box {{
            background-color: #F0FDFA;
            border-left: 3px solid #0D9488;
            padding: 8px 10px;
            font-size: 12px;
            color: #134E4A;
            margin-bottom: 8px;
        }}
        ul {{
            margin: 0;
            padding-left: 18px;
        }}
        .referral-box {{
            background-color: #EFF6FF;
            border: 1px dashed #3B82F6;
            padding: 8px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 11px;
        }}
        .footer {{
            margin-top: 20px;
            border-top: 1px solid #CBD5E1;
            padding-top: 8px;
            font-size: 10px;
            color: #64748B;
        }}
        .sig-table {{
            width: 100%;
            margin-top: 30px;
            border-collapse: collapse;
        }}
        .sig-table td {{
            text-align: center;
            font-size: 11px;
            color: #334155;
        }}
    </style>
    </head>
    <body>
        <div class="header">
            <div class="title">National Health Mission (NHM)</div>
            <div class="subtitle">Primary Health Centre (PHC) &bull; ASHA Field Health Assessment Slip</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 3px;">Vyoma Offline Medical AI &bull; Village Field Unit</div>
        </div>

        {triage_badge}

        <table class="meta-table">
            <tr>
                <td class="meta-label">Citizen Name:</td>
                <td><b>{p_name}</b></td>
                <td class="meta-label">Assessment Date:</td>
                <td>{now_str}</td>
            </tr>
            <tr>
                <td class="meta-label">Age / Gender:</td>
                <td>{p_age} Years / {p_gender}</td>
                <td class="meta-label">ABHA ID:</td>
                <td><b>{p_abha}</b></td>
            </tr>
            <tr>
                <td class="meta-label">Village / Locality:</td>
                <td>{p_village}</td>
                <td class="meta-label">Phone Contact:</td>
                <td>{p_phone}</td>
            </tr>
            <tr>
                <td class="meta-label">Residential Address:</td>
                <td colspan="3">{p_address}</td>
            </tr>
            <tr>
                <td class="meta-label">Known Chronic Conditions:</td>
                <td><span style="color: #991B1B; font-weight: 600;">{p_conds}</span></td>
                <td class="meta-label">Allergies:</td>
                <td><span style="color: #C2410C; font-weight: 600;">{p_allergies}</span></td>
            </tr>
        </table>

        <div class="section-title">Reported Symptoms (Vernacular Voice Input)</div>
        <div style="font-style: italic; color: #334155; margin-bottom: 8px; padding-left: 4px;">
            &ldquo;{query_text}&rdquo;
        </div>

        <div class="section-title">Clinical Assessment & Protocol Guidance</div>
        <div class="summary-box">
            {summary}
        </div>

        <div class="section-title">Recommended Non-Pharmacological Care & Next Steps</div>
        <ul>
            {actions_html}
        </ul>

        <div class="section-title" style="color: #B91C1C; border-bottom-color: #FECACA;">Danger Warning Signs (Watch Closely)</div>
        <ul>
            {warnings_html}
        </ul>

        <div class="referral-box">
            <b>🏥 Primary Health Center Referral:</b><br>
            {referral}
        </div>

        <div style="font-size: 9px; color: #94A3B8; margin-top: 8px;">
            <b>Guideline Citations:</b> {sources}
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 50%;">
                    __________________________________<br>
                    <b>ASHA Field Health Worker</b><br>
                    Unit ID: ASHA-FIELD-TN-04
                </td>
                <td style="width: 50%;">
                    __________________________________<br>
                    <b>Medical Officer / PHC Staff</b><br>
                    Sundarapuram Primary Health Centre
                </td>
            </tr>
        </table>

        <div class="footer" style="text-align: center;">
            This document is a village-level clinical triage advisory generated locally on the Vyoma Edge AI terminal.
            Not a substitute for emergency physician diagnosis. In acute deterioration, dial 108 / 112 immediately.
        </div>
    </body>
    </html>
    """
    return html


def _create_qprinter() -> Optional[Any]:
    """Instantiates a QPrinter safely across PyQt5, PyQt6, and PySide6."""
    if not HAS_QT or QPrinter is None:
        return None
    try:
        # PyQt6 scoped enum
        mode = getattr(getattr(QPrinter, "PrinterMode", None), "HighResolution", None)
        if mode is not None:
            return QPrinter(mode)
        # PyQt5 / PySide6 enum
        mode = getattr(QPrinter, "HighResolution", None)
        if mode is not None:
            return QPrinter(mode)
        return QPrinter()
    except Exception:
        return QPrinter()


def _set_pdf_format(printer: Any, pdf_path: str) -> None:
    """Configures QPrinter for PDF output safely across Qt versions."""
    try:
        fmt = getattr(getattr(QPrinter, "OutputFormat", None), "PdfFormat", None)
        if fmt is not None:
            printer.setOutputFormat(fmt)
        elif hasattr(QPrinter, "PdfFormat"):
            printer.setOutputFormat(QPrinter.PdfFormat)
    except Exception:
        pass
    printer.setOutputFileName(str(pdf_path))


def print_clinical_report(
    parent_widget: Optional[QWidget],
    patient_data: Optional[Dict[str, Any]],
    clinical_result: Dict[str, Any],
    language: str = "en"
) -> Tuple[bool, str]:
    """
    Sends clinical assessment slip directly to an attached USB printer.
    If no physical printer is plugged in, automatically exports a high-resolution PDF backup.
    Returns:
        (success: bool, message: str)
    """
    if not HAS_QT:
        return False, "Qt runtime not loaded."

    # 1. Generate HTML slip
    html_content = generate_report_html(patient_data, clinical_result, language)

    # 2. Prepare timestamped PDF backup path
    reports_dir = settings.resolve_path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    clean_name = (patient_data.get("name") if patient_data else "Citizen").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = reports_dir / f"ASHA_Report_{clean_name}_{timestamp}.pdf"

    doc = QTextDocument()
    doc.setHtml(html_content)

    # 3. Detect USB / hardware printer
    usb_printer_name = find_usb_printer()
    printed_to_hardware = False

    if QPrinter is not None:
        try:
            printer = _create_qprinter()
            if printer is not None and usb_printer_name:
                printer.setPrinterName(usb_printer_name)
                if hasattr(doc, "print_"):
                    doc.print_(printer)
                elif hasattr(doc, "print"):
                    doc.print(printer)
                printed_to_hardware = True
                logger.info(f"Dispatched clinical slip directly to USB printer: '{usb_printer_name}'")
        except Exception as e:
            logger.warning(f"Direct USB printer job note: {e}. Falling back to PDF export.")

    # 4. Save offline PDF copy regardless (for ASHA field records)
    try:
        pdf_printer = _create_qprinter()
        if pdf_printer is not None:
            _set_pdf_format(pdf_printer, str(pdf_path))
            if hasattr(doc, "print_"):
                doc.print_(pdf_printer)
            elif hasattr(doc, "print"):
                doc.print(pdf_printer)
            logger.info(f"Saved offline PDF clinical slip to {pdf_path}")
    except Exception as e:
        logger.error(f"Error creating PDF slip: {e}")

    # 5. User feedback message
    if printed_to_hardware:
        msg = f"Report printed to USB device: '{usb_printer_name}'\nArchived copy: {pdf_path.name}"
    else:
        msg = f"Clinical Report saved as PDF:\n{pdf_path.name}"

    return True, msg

