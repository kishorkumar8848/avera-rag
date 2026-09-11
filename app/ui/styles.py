"""
AVERA Touchscreen Kiosk QSS Stylesheet.
Clean, modern, accessible Medical White & Royal Blue design system
optimized for touchscreen kiosks, field tablets, and desktop displays.
"""

KIOSK_STYLESHEET = """
/* Base Window & Global Fonts */
QWidget {
    background-color: #F8FAFC;
    color: #1E293B;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Ubuntu', sans-serif;
    font-size: 16px;
}

/* Top Navigation Bar */
QFrame#TopBar {
    background-color: #FFFFFF;
    border-bottom: 1.5px solid #E2E8F0;
    min-height: 64px;
    max-height: 64px;
}

QLabel#TopBarBrand {
    font-size: 24px;
    font-weight: 800;
    color: #1D4ED8;
    letter-spacing: 0.5px;
}

QLabel#TopBarTagline {
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
}

QLabel#TopBarSubHeader {
    font-size: 15px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#TopBarMotto {
    font-size: 12px;
    color: #64748B;
}

QFrame#TopBarDivider {
    background-color: #E2E8F0;
    width: 1px;
    max-width: 1px;
    min-height: 36px;
    max-height: 36px;
}

QLabel#TopBarClock {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
}

QLabel#TopBarTelemetry {
    font-size: 12px;
    color: #64748B;
    background-color: #F1F5F9;
    padding: 4px 8px;
    border-radius: 6px;
}

QPushButton#NavBtn {
    min-height: 40px;
    max-height: 40px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
}

QPushButton#NavBtn:hover {
    background-color: #EFF6FF;
    border-color: #3B82F6;
    color: #1D4ED8;
}

QPushButton#PatientBadgeBtn {
    min-height: 40px;
    max-height: 40px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1D4ED8;
}

QPushButton#PatientBadgeBtn:hover {
    background-color: #DBEAFE;
    border-color: #2563EB;
}

/* Push Buttons - Touch Friendly (min 52-64px height) */
QPushButton {
    background-color: #FFFFFF;
    color: #1E293B;
    border: 1.5px solid #CBD5E1;
    border-radius: 12px;
    padding: 10px 20px;
    font-size: 17px;
    font-weight: 600;
    min-height: 52px;
}

QPushButton:hover {
    background-color: #EFF6FF;
    border-color: #3B82F6;
    color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #DBEAFE;
    border-color: #2563EB;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Primary Action Buttons */
QPushButton#PrimaryBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    font-size: 18px;
    font-weight: 700;
    min-height: 56px;
    border-radius: 12px;
}

QPushButton#PrimaryBtn:hover {
    background-color: #1D4ED8;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #1E40AF;
}

QPushButton#PrimaryBtn:disabled {
    background-color: #93C5FD;
    color: #EFF6FF;
}

/* Active Language Card (Blue Background like Reference Image) */
QPushButton#ActiveLangCard {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1.5px solid #2563EB;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 700;
    text-align: left;
    padding-left: 20px;
    padding-right: 20px;
}

QPushButton#ActiveLangCard:hover {
    background-color: #1D4ED8;
    border-color: #1D4ED8;
}

/* Inactive Language Card (White with Clean Border and Chevron) */
QPushButton#LangCard {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1.5px solid #E2E8F0;
    border-radius: 14px;
    font-size: 18px;
    font-weight: 600;
    text-align: left;
    padding-left: 20px;
    padding-right: 20px;
}

QPushButton#LangCard:hover {
    background-color: #F0F7FF;
    border-color: #93C5FD;
    color: #1D4ED8;
}

QPushButton#LangCard:pressed {
    background-color: #DBEAFE;
}

/* Microphone Push-to-Talk / 10s Click Button */
QPushButton#MicBtn {
    background-color: #EFF6FF;
    color: #2563EB;
    border: 3px solid #2563EB;
    border-radius: 36px;
    font-size: 20px;
    font-weight: 700;
    min-height: 68px;
    padding: 10px 24px;
}

QPushButton#MicBtn:hover {
    background-color: #DBEAFE;
    border-color: #1D4ED8;
    color: #1D4ED8;
}

QPushButton#MicBtn:checked, QPushButton#MicBtn:pressed {
    background-color: #EF4444;
    color: #FFFFFF;
    border-color: #DC2626;
}

/* Navigation Buttons (Top Bar) */
QPushButton#NavBtn {
    background-color: #F8FAFC;
    color: #334155;
    border: 1.5px solid #E2E8F0;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    min-height: 40px;
    min-width: 40px;
    padding: 6px 14px;
}

QPushButton#NavBtn:hover {
    background-color: #EFF6FF;
    border-color: #93C5FD;
    color: #1D4ED8;
}

QPushButton#NavBtn:pressed {
    background-color: #DBEAFE;
}

QPushButton#NavBtn:disabled {
    background-color: #F8FAFC;
    color: #CBD5E1;
    border-color: #F1F5F9;
}

/* Citizen Top-Bar Badge */
QPushButton#PatientBadgeBtn {
    background-color: #F0FDF4;
    color: #166534;
    border: 1.5px solid #BBF7D0;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 700;
    padding: 6px 14px;
    min-height: 40px;
}

QPushButton#PatientBadgeBtn:hover {
    background-color: #DCFCE7;
    border-color: #86EFAC;
}

/* Result Cards & Information Panels */
QFrame#CardFrame {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px;
}

QLabel#CardHeader {
    font-size: 18px;
    font-weight: 700;
    color: #1D4ED8;
}

QLabel#CardBody {
    font-size: 16px;
    line-height: 1.5;
    color: #1E293B;
}

QLabel#SourceCitation {
    font-size: 13px;
    color: #64748B;
    font-style: italic;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #F1F5F9;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 6px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

/* Citizen Information Strip */
QFrame#CitizenBar {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
    padding: 8px 16px;
    min-height: 50px;
}

QLabel#CitizenName {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
}

QLabel#CitizenMeta {
    font-size: 14px;
    color: #64748B;
}

/* Action Buttons (Print & New Assessment) */
QPushButton#PrintBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 700;
    min-height: 56px;
    padding: 10px 24px;
}

QPushButton#PrintBtn:hover {
    background-color: #1D4ED8;
}

QPushButton#PrintBtn:pressed {
    background-color: #1E40AF;
}

QPushButton#NewAssessmentBtn {
    background-color: #059669;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 700;
    min-height: 56px;
    padding: 10px 24px;
}

QPushButton#NewAssessmentBtn:hover {
    background-color: #047857;
}

QPushButton#NewAssessmentBtn:pressed {
    background-color: #065F46;
}

/* Patient Summary Card at End of Consultation */
QFrame#PatientSummaryCard {
    background-color: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 12px;
    padding: 16px;
    margin-top: 8px;
}

/* Age & Risk Guidance Card */
QFrame#AgeGuidanceCard {
    background-color: #FFFBEB;
    border: 2px solid #F59E0B;
    border-radius: 12px;
    padding: 14px;
    margin-top: 8px;
}

QLabel#AgeGuidanceTitle {
    font-size: 16px;
    font-weight: 700;
    color: #92400E;
}

QLabel#AgeGuidanceBody {
    font-size: 15px;
    color: #78350F;
    line-height: 1.5;
}

/* Emergency Red Banner */
QFrame#EmergencyBanner {
    background-color: #FEF2F2;
    border: 2px solid #EF4444;
    border-radius: 12px;
    padding: 16px;
}

QLabel#EmergencyText {
    color: #991B1B;
    font-size: 18px;
    font-weight: 700;
}

/* Text Inputs & Search Boxes */
QLineEdit {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1.5px solid #CBD5E1;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 16px;
}

QLineEdit:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}

/* Table Widget for Citizen Registry Dialog */
QTableWidget {
    background-color: #FFFFFF;
    gridline-color: #F1F5F9;
    color: #0F172A;
    border: 1.5px solid #E2E8F0;
    border-radius: 10px;
    selection-background-color: #EFF6FF;
    selection-color: #1D4ED8;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    padding: 10px;
    font-weight: 700;
    border: 1px solid #E2E8F0;
}

/* Retake & Symptom Verification Card */
QFrame#RetakeCard {
    background-color: #FFFBEB;
    border: 2px solid #F59E0B;
    border-radius: 14px;
    padding: 20px;
    margin-top: 8px;
}

QLabel#RetakeTitle {
    font-size: 20px;
    font-weight: 800;
    color: #B45309;
}

QLabel#RetakeCapturedText {
    font-size: 15px;
    color: #334155;
    background-color: #FFFFFF;
    border: 1.5px solid #FDE68A;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0px;
    line-height: 1.4;
}

QLabel#RetakeBody {
    font-size: 16px;
    color: #92400E;
    line-height: 1.5;
    margin: 4px 0px;
}

QPushButton#RetakeBtn {
    background-color: #D97706;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-size: 18px;
    font-weight: 700;
    min-height: 56px;
    margin-top: 12px;
}

QPushButton#RetakeBtn:hover {
    background-color: #B45309;
}

QPushButton#RetakeBtn:pressed {
    background-color: #92400E;
}
"""
