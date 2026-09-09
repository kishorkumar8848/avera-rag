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
"""
