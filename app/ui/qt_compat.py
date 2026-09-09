"""
Qt Compatibility Bridge for PySide6 and PyQt6.
Seamlessly supports both Jetson Linux runtime (PySide6) and Laptop development (PyQt6).
"""

from __future__ import annotations
import sys

HAS_QT = False
QT_BINDING = None

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, Signal, Slot
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QStackedWidget, QLabel, QPushButton, QFrame,
        QScrollArea, QProgressBar, QTextEdit
    )
    from PySide6.QtGui import QImage, QPixmap, QFont, QIcon, QColor
    HAS_QT = True
    QT_BINDING = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import Qt, QTimer, QThreadPool, QRunnable, QObject, pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QGridLayout, QStackedWidget, QLabel, QPushButton, QFrame,
            QScrollArea, QProgressBar, QTextEdit
        )
        from PyQt6.QtGui import QImage, QPixmap, QFont, QIcon, QColor
        HAS_QT = True
        QT_BINDING = "PyQt6"
    except ImportError:
        HAS_QT = False
        QT_BINDING = None
        class QMainWindow: pass
        class QWidget: pass
        class QObject: pass
        class QRunnable: pass
        Signal = None
        Slot = None

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
    except Exception:
        pass
