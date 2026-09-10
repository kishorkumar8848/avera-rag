"""
Touchscreen Kiosk QSS Stylesheet optimized for Waveshare 7-inch 1024x600 display.
High contrast, large touch targets (60-80px), legible fonts, accessible colors.
"""

KIOSK_STYLESHEET = """
QWidget {
    background-color: #0B132B;
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 16px;
}

/* Top Navigation Bar */
QFrame#TopBar {
    background-color: #1C2541;
    border-bottom: 2px solid #3A506B;
    min-height: 56px;
    max-height: 56px;
}

QLabel#TopBarTitle {
    font-size: 20px;
    font-weight: bold;
    color: #00E8C6;
}

QLabel#TopBarStatus {
    font-size: 14px;
    color: #94A3B8;
}

/* Push Buttons - Minimum 60-80px touch target */
QPushButton {
    background-color: #1C2541;
    color: #F8FAFC;
    border: 2px solid #3A506B;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 18px;
    font-weight: 600;
    min-height: 58px;
}

QPushButton:hover {
    background-color: #3A506B;
    border-color: #00E8C6;
}

QPushButton:pressed {
    background-color: #00E8C6;
    color: #0B132B;
}

/* Primary Action Buttons */
QPushButton#PrimaryBtn {
    background-color: #00E8C6;
    color: #0B132B;
    border: none;
    font-size: 20px;
    font-weight: bold;
    min-height: 64px;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #00B49F;
}

/* Microphone Push-to-Talk Button */
QPushButton#MicBtn {
    background-color: #1C2541;
    color: #00E8C6;
    border: 4px solid #00E8C6;
    border-radius: 40px;
    font-size: 22px;
    font-weight: bold;
    min-width: 80px;
    min-height: 80px;
}

QPushButton#MicBtn:checked, QPushButton#MicBtn:pressed {
    background-color: #EF4444;
    color: #FFFFFF;
    border-color: #F87171;
}

/* Emergency Red Button / Banner */
QFrame#EmergencyBanner {
    background-color: #7F1D1D;
    border: 2px solid #EF4444;
    border-radius: 12px;
    padding: 14px;
}

QLabel#EmergencyText {
    color: #FEF2F2;
    font-size: 18px;
    font-weight: bold;
}

/* Navigation Icons / Buttons */
QPushButton#NavBtn {
    background-color: #1C2541;
    border: 1px solid #3A506B;
    border-radius: 8px;
    font-size: 16px;
    min-height: 44px;
    min-width: 44px;
    padding: 6px 14px;
}

/* Result Cards & Panels */
QFrame#CardFrame {
    background-color: #1C2541;
    border: 1px solid #3A506B;
    border-radius: 14px;
    padding: 16px;
}

QLabel#CardHeader {
    font-size: 18px;
    font-weight: bold;
    color: #00E8C6;
}

QLabel#CardBody {
    font-size: 16px;
    line-height: 1.4;
    color: #E2E8F0;
}

QLabel#SourceCitation {
    font-size: 13px;
    color: #94A3B8;
    font-style: italic;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #0B132B;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: #3A506B;
    border-radius: 7px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #00E8C6;
}

/* Citizen Information Strip */
QFrame#CitizenBar {
    background-color: #111C38;
    border: 1px solid #2A3C60;
    border-radius: 10px;
    padding: 6px 14px;
    min-height: 48px;
}

QLabel#CitizenName {
    font-size: 16px;
    font-weight: bold;
    color: #38BDF8;
}

QLabel#CitizenMeta {
    font-size: 13px;
    color: #94A3B8;
}

/* Action Buttons */
QPushButton#PrintBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #60A5FA;
    border-radius: 12px;
    font-size: 17px;
    font-weight: bold;
    min-height: 58px;
    padding: 10px 24px;
}

QPushButton#PrintBtn:hover {
    background-color: #1D4ED8;
    border-color: #93C5FD;
}

QPushButton#PrintBtn:pressed {
    background-color: #1E40AF;
}

QPushButton#NewAssessmentBtn {
    background-color: #059669;
    color: #FFFFFF;
    border: 2px solid #34D399;
    border-radius: 12px;
    font-size: 18px;
    font-weight: bold;
    min-height: 60px;
    padding: 10px 24px;
}

QPushButton#NewAssessmentBtn:hover {
    background-color: #047857;
    border-color: #6EE7B7;
}

QPushButton#NewAssessmentBtn:pressed {
    background-color: #065F46;
}

/* Patient Summary Card at End of Consultation */
QFrame#PatientSummaryCard {
    background-color: #0F172A;
    border: 2px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin-top: 8px;
}

/* Age & Risk Guidance Card */
QFrame#AgeGuidanceCard {
    background-color: #422006;
    border: 2px solid #F59E0B;
    border-radius: 12px;
    padding: 14px;
    margin-top: 6px;
}

QLabel#AgeGuidanceTitle {
    font-size: 16px;
    font-weight: bold;
    color: #FBBF24;
}

QLabel#AgeGuidanceBody {
    font-size: 15px;
    color: #FEF3C7;
    line-height: 1.4;
}

/* Text Inputs & Search Boxes */
QLineEdit {
    background-color: #1C2541;
    color: #F8FAFC;
    border: 2px solid #3A506B;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 16px;
}

QLineEdit:focus {
    border-color: #00E8C6;
}

/* Table Widget for Citizen Registry Dialog */
QTableWidget {
    background-color: #0B132B;
    gridline-color: #1E293B;
    color: #F1F5F9;
    border: 1px solid #3A506B;
    border-radius: 8px;
    selection-background-color: #0D9488;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #1C2541;
    color: #00E8C6;
    padding: 8px;
    font-weight: bold;
    border: 1px solid #2D3748;
}
"""

