"""
Qt Compatibility Bridge for PySide6, PyQt6, and PyQt5.
Seamlessly supports Jetson Linux runtime (system PyQt5 / PySide6) and Laptop development (PyQt6).
Includes QtPrintSupport for direct USB printer hardware and QTextDocument PDF generation.
"""

from __future__ import annotations
import sys
import os

# Clean cv2 plugin path if OpenCV poisoned QT_QPA_PLATFORM_PLUGIN_PATH
if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ and "cv2" in os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]:
    del os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]

HAS_QT = False
QT_BINDING = None

# Fallback dummy classes if no Qt is present
class _Dummy:
    pass

QMainWindow = _Dummy
QWidget = _Dummy
QObject = _Dummy
QRunnable = _Dummy
QDialog = _Dummy
QPainter = _Dummy
QPen = _Dummy
QBrush = _Dummy
QColor = _Dummy
Signal = None
Slot = None
QTextDocument = None
QPrinter = None
QPrintDialog = None
QPrinterInfo = None

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, Signal, Slot
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QStackedWidget, QLabel, QPushButton, QFrame,
        QScrollArea, QProgressBar, QTextEdit, QLineEdit, QComboBox,
        QDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PySide6.QtGui import QImage, QPixmap, QFont, QIcon, QColor, QTextDocument, QPainter, QPen, QBrush
    try:
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
    except ImportError:
        pass
    HAS_QT = True
    QT_BINDING = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QGridLayout, QStackedWidget, QLabel, QPushButton, QFrame,
            QScrollArea, QProgressBar, QTextEdit, QLineEdit, QComboBox,
            QDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
        )
        from PyQt6.QtGui import QImage, QPixmap, QFont, QIcon, QColor, QTextDocument, QPainter, QPen, QBrush
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
        except ImportError:
            pass
        HAS_QT = True
        QT_BINDING = "PyQt6"
    except ImportError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
            from PyQt5.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot
            from PyQt5.QtWidgets import (
                QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                QGridLayout, QStackedWidget, QLabel, QPushButton, QFrame,
                QScrollArea, QProgressBar, QTextEdit, QLineEdit, QComboBox,
                QDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
            )
            from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon, QColor, QTextDocument, QPainter, QPen, QBrush
            try:
                from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
            except ImportError:
                pass
            HAS_QT = True
            QT_BINDING = "PyQt5"
        except ImportError:
            HAS_QT = False
            QT_BINDING = None

# Backward compatibility enum aliases for PyQt6 (which scopes enums strictly)
if HAS_QT and QT_BINDING == "PyQt6":
    try:
        if hasattr(Qt, "AlignmentFlag"):
            Qt.AlignCenter = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            Qt.AlignLeft = Qt.AlignmentFlag.AlignLeft
            Qt.AlignRight = Qt.AlignmentFlag.AlignRight
            Qt.AlignTop = Qt.AlignmentFlag.AlignTop
            Qt.AlignBottom = Qt.AlignmentFlag.AlignBottom
        if hasattr(Qt, "CursorShape"):
            Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
            Qt.ArrowCursor = Qt.CursorShape.ArrowCursor
            Qt.WaitCursor = Qt.CursorShape.WaitCursor
        if hasattr(Qt, "AspectRatioMode"):
            Qt.KeepAspectRatio = Qt.AspectRatioMode.KeepAspectRatio
            Qt.IgnoreAspectRatio = Qt.AspectRatioMode.IgnoreAspectRatio
        if hasattr(Qt, "TransformationMode"):
            Qt.SmoothTransformation = Qt.TransformationMode.SmoothTransformation
            Qt.FastTransformation = Qt.TransformationMode.FastTransformation
        if hasattr(Qt, "ScrollBarPolicy"):
            Qt.ScrollBarAlwaysOff = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            Qt.ScrollBarAlwaysOn = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
            Qt.ScrollBarAsNeeded = Qt.ScrollBarPolicy.ScrollBarAsNeeded
        if hasattr(Qt, "Key"):
            Qt.Key_F11 = Qt.Key.Key_F11
            Qt.Key_Escape = Qt.Key.Key_Escape
    except Exception:
        pass
elif HAS_QT and QT_BINDING in ["PyQt5", "PySide6"]:
    try:
        if not hasattr(Qt, "Key_F11"):
            Qt.Key_F11 = getattr(QtCore.Qt, "Key_F11", 0x0100003a)
        if not hasattr(Qt, "Key_Escape"):
            Qt.Key_Escape = getattr(QtCore.Qt, "Key_Escape", 0x01000000)
    except Exception:
        pass
