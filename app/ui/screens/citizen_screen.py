"""
Screen 2: Resident / Citizen Selection Screen for AVERA Kiosk.
Provides a clean, high-contrast, touch-friendly patient selector with real-time search
across village registry records (Name, Age, ABHA, Village, Conditions).
"""

from typing import Callable, List, Optional

from app.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, Qt, HAS_QT
)

from app.safety.patient_registry import patient_registry, PatientRecord


class CitizenScreen(QWidget if HAS_QT else object):
    """
    Dedicated screen in the kiosk flow for selecting a village resident
    before acquiring vitals and beginning medical assessment.
    """

    def __init__(self, on_citizen_selected: Callable[[PatientRecord], None], parent=None):
        if HAS_QT:
            super().__init__(parent)
        self.on_citizen_selected = on_citizen_selected
        self.current_records: List[PatientRecord] = []
        self.selected_patient: Optional[PatientRecord] = None

        if HAS_QT:
            self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(16)

        # Header Title Area
        header_box = QWidget()
        h_layout = QVBoxLayout(header_box)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        title = QLabel("Select Village Resident for Assessment")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;")
        h_layout.addWidget(title)

        subtitle = QLabel("Select citizen from offline village health registry or search by name, age, or ABHA ID")
        subtitle.setStyleSheet("font-size: 15px; color: #64748B; font-weight: 500;")
        h_layout.addWidget(subtitle)

        layout.addWidget(header_box)

        # Search Bar Row
        search_card = QFrame()
        search_card.setObjectName("CardFrame")
        s_layout = QHBoxLayout(search_card)
        s_layout.setContentsMargins(14, 10, 14, 10)
        s_layout.setSpacing(12)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 20px; background: transparent;")
        s_layout.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search village residents (e.g., 'kishor', '50', 'sundarapuram', '91-4432')...")
        self.search_edit.setStyleSheet(
            "font-size: 16px; border: none; background: transparent; padding: 6px; color: #0F172A;"
        )
        self.search_edit.textChanged.connect(self._on_search_changed)
        s_layout.addWidget(self.search_edit, stretch=1)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("NavBtn")
        clear_btn.setMinimumHeight(40)
        clear_btn.clicked.connect(lambda: self.search_edit.clear())
        s_layout.addWidget(clear_btn)

        layout.addWidget(search_card)

        # Table of Citizens
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Citizen Name", "Age / Group", "Gender", "Village", "Known Conditions", "ABHA ID"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows if hasattr(QTableWidget, "SelectRows") else 1)
        self.table.setSelectionMode(QTableWidget.SingleSelection if hasattr(QTableWidget, "SingleSelection") else 1)
        self.table.itemDoubleClicked.connect(self._on_confirm_selected)
        self.table.setStyleSheet(
            "QTableWidget { font-size: 15px; border-radius: 12px; gridline-color: #E2E8F0; }"
            "QHeaderView::section { background-color: #F1F5F9; font-weight: 700; color: #1E293B; font-size: 15px; padding: 8px; }"
            "QTableWidget::item { padding: 10px; }"
            "QTableWidget::item:selected { background-color: #DBEAFE; color: #1E40AF; }"
        )

        header = self.table.horizontalHeader()
        if hasattr(header, "setSectionResizeMode"):
            try:
                header.setSectionResizeMode(0, QHeaderView.ResizeToContents if hasattr(QHeaderView, "ResizeToContents") else 1)
                header.setSectionResizeMode(4, QHeaderView.Stretch if hasattr(QHeaderView, "Stretch") else 1)
            except Exception:
                pass
        layout.addWidget(self.table, stretch=1)

        # Bottom Action Bar
        action_row = QHBoxLayout()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #64748B; font-size: 14px; font-weight: 600;")
        action_row.addWidget(self.status_lbl)

        action_row.addStretch()

        proceed_btn = QPushButton("Confirm Resident & Take Vitals  ➔")
        proceed_btn.setObjectName("PrimaryBtn")
        proceed_btn.setMinimumHeight(52)
        proceed_btn.setCursor(Qt.PointingHandCursor)
        proceed_btn.clicked.connect(self._on_confirm_selected)
        action_row.addWidget(proceed_btn)

        layout.addLayout(action_row)

        # Initial Population
        self._populate_table(patient_registry.get_all())

    def _populate_table(self, patients: List[PatientRecord]):
        self.current_records = patients
        self.table.setRowCount(len(patients))
        for row, p in enumerate(patients):
            conds_str = ", ".join(p.chronic_conditions) if p.chronic_conditions else "None Reported"
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.age_display_badge))
            self.table.setItem(row, 2, QTableWidgetItem(p.gender))
            self.table.setItem(row, 3, QTableWidgetItem(p.village))
            self.table.setItem(row, 4, QTableWidgetItem(conds_str))
            self.table.setItem(row, 5, QTableWidgetItem(p.abha_id))

        self.status_lbl.setText(f"Showing {len(patients)} registered village residents")
        if patients:
            self.table.selectRow(0)

    def _on_search_changed(self, text: str):
        matches = patient_registry.search(text.strip())
        self._populate_table(matches)

    def _on_confirm_selected(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.current_records):
            self.selected_patient = self.current_records[row]
            if self.on_citizen_selected:
                self.on_citizen_selected(self.selected_patient)

    def reset_selection(self):
        """Clears search filter and selection for fresh resident entry."""
        if hasattr(self, "search_edit"):
            self.search_edit.clear()
        if hasattr(self, "table"):
            self.table.clearSelection()
        self.selected_patient = None
        self._populate_table(patient_registry.get_all())
