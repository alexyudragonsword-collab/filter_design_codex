import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.ui.app import create_application
from filter_design.ui.main_window import MainWindow
from filter_design.ui.specification_panel import SpecificationPanel


def application() -> QApplication:
    return create_application(["test-filter-design"])


def test_specification_panel_roundtrip():
    application()
    panel = SpecificationPanel()
    specification = FilterSpecification(
        ResponseType.BANDPASS,
        Approximation.CHEBYSHEV1,
        (1e6, 2e6),
        (0.5e6, 3e6),
        0.25,
        45,
        75,
        75,
        7,
    )
    panel.set_specification(specification)
    assert panel.specification() == specification
    assert panel.pass2.isEnabled()
    assert panel.stop2.isEnabled()


def test_main_window_completes_design_in_qthread():
    app = application()
    window = MainWindow()
    loop = QEventLoop()
    completed = []

    def finish(design):
        completed.append(design)
        loop.quit()

    window.design_completed.connect(finish)
    QTimer.singleShot(0, window.start_design)
    QTimer.singleShot(10_000, loop.quit)
    loop.exec()
    assert completed, "Qt design worker timed out"

    cleanup = QEventLoop()
    if window._thread is not None:
        window._thread.finished.connect(cleanup.quit)
        QTimer.singleShot(5_000, cleanup.quit)
        cleanup.exec()
    app.processEvents()

    window.resize(1100, 720)
    window.show()
    app.processEvents()
    snapshot = window.grab()
    assert not snapshot.isNull()
    assert snapshot.width() == 1100

    assert window.design is completed[0]
    assert window.component_model.rowCount() == window.design.synthesis.order
    assert window.export_csv_action.isEnabled()
    assert "dB" in window.pass_metric[1].text()
    window.close()
