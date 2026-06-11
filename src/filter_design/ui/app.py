"""Qt for Python application entry point."""
from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication, QTimer, Qt
from PySide6.QtWidgets import QApplication

from filter_design import __version__

from .main_window import MainWindow
from .theme import apply_theme


def create_application(argv: list[str] | None = None) -> QApplication:
    """Create or return the process-wide QApplication."""
    existing = QApplication.instance()
    if existing is not None:
        return existing
    QCoreApplication.setOrganizationName("OpenFilterDesigner")
    QCoreApplication.setApplicationName("OpenFilterDesigner")
    QCoreApplication.setApplicationVersion(__version__)
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    application = QApplication(argv if argv is not None else sys.argv)
    apply_theme(application)
    return application


def main() -> int:
    application = create_application()
    window = MainWindow()
    window.show()
    QTimer.singleShot(0, window.start_design)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
