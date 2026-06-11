"""Application-wide Qt palette and stylesheet."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


STYLE_SHEET = """
QMainWindow, QWidget { background: #f5f7fa; color: #172033; }
QFrame#Header { background: #102a43; border-radius: 8px; }
QFrame#Header QLabel { background: transparent; color: white; }
QGroupBox {
    background: white; border: 1px solid #d7e0ea; border-radius: 8px;
    font-weight: 600; margin-top: 12px; padding-top: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
    background: white; border: 1px solid #bcc9d6; border-radius: 5px;
    min-height: 30px; padding: 0 7px;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 2px solid #1677b8;
}
QPushButton {
    background: #e8eef5; border: 1px solid #c5d1dd; border-radius: 5px;
    min-height: 32px; padding: 0 14px; font-weight: 600;
}
QPushButton:hover { background: #dbe8f4; }
QPushButton#PrimaryButton { background: #1677b8; border-color: #1677b8; color: white; }
QPushButton#PrimaryButton:hover { background: #0f659f; }
QPushButton:disabled { color: #8b98a5; background: #edf1f5; }
QTabWidget::pane { background: white; border: 1px solid #d7e0ea; border-radius: 5px; }
QTabBar::tab { background: #e8eef5; padding: 9px 18px; margin-right: 2px; }
QTabBar::tab:selected { background: white; color: #0f659f; font-weight: 600; }
QTableView { background: white; alternate-background-color: #f5f8fb; gridline-color: #e1e7ee; }
QHeaderView::section { background: #e8eef5; border: 0; border-right: 1px solid #d3dce6; padding: 7px; font-weight: 600; }
QStatusBar { background: #edf2f7; }
QProgressBar { border: 0; background: #dce5ee; border-radius: 3px; max-height: 6px; }
QProgressBar::chunk { background: #1677b8; border-radius: 3px; }
"""


def apply_theme(application: QApplication) -> None:
    """Apply a predictable light theme across desktop platforms."""
    application.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f7fa"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f5f8fb"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1677b8"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    application.setPalette(palette)
    application.setStyleSheet(STYLE_SHEET)
