"""Main Qt window for the filter-design workflow."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Qt, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from filter_design.domain.project import FilterProject
from filter_design.exporters.csv_export import export_csv
from filter_design.exporters.report import export_html
from filter_design.exporters.spice import export_spice
from filter_design.exporters.touchstone import export_touchstone
from filter_design.workflow import Design, suggested_sweep

from .active_rc_tab import ActiveRCTab
from .component_model import ComponentTableModel
from .leapfrog_tab import LeapfrogTab
from .response_plot import ResponsePlot
from .schematic_view import SchematicView
from .specification_panel import SpecificationPanel
from .worker import DesignWorker


class MainWindow(QMainWindow):
    """Coordinates project, synthesis, analysis, and export UI operations."""

    design_completed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Open Filter Designer — Qt")
        self.setMinimumSize(1024, 680)
        self.resize(1240, 800)
        self.design: Design | None = None
        self.project_path: Path | None = None
        self._thread: QThread | None = None
        self._worker: DesignWorker | None = None
        self._settings = QSettings("OpenFilterDesigner", "OpenFilterDesigner")

        self._build_actions()
        self._build_menu()
        self._build_content()
        self._build_status_bar()
        self._restore_window_state()

    def _build_actions(self) -> None:
        self.open_action = QAction("Open Project…", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_project)
        self.save_action = QAction("Save Project…", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_project)
        self.quit_action = QAction("Exit", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.quit_action.triggered.connect(self.close)

        self.export_csv_action = QAction("Export Response CSV…", self)
        self.export_csv_action.triggered.connect(lambda: self.export_design("csv"))
        self.export_touchstone_action = QAction("Export Touchstone…", self)
        self.export_touchstone_action.triggered.connect(lambda: self.export_design("s2p"))
        self.export_spice_action = QAction("Export SPICE Netlist…", self)
        self.export_spice_action.triggered.connect(lambda: self.export_design("cir"))
        self.export_report_action = QAction("Export HTML Report…", self)
        self.export_report_action.triggered.connect(lambda: self.export_design("html"))
        self.export_actions = (
            self.export_csv_action,
            self.export_touchstone_action,
            self.export_spice_action,
            self.export_report_action,
        )
        for action in self.export_actions:
            action.setEnabled(False)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addActions(self.export_actions)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self.about_action)

    def _build_content(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(10)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QVBoxLayout(header)
        title = QLabel("Open Filter Designer")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel("Specification  →  Synthesis  →  LC Network  →  S-Parameter Verification")
        subtitle.setStyleSheet("color: #c7d8e8; font-size: 13px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        outer.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.specification_panel = SpecificationPanel()
        self.specification_panel.setMinimumWidth(330)
        self.specification_panel.setMaximumWidth(410)
        self.specification_panel.design_requested.connect(self.start_design)
        splitter.addWidget(self.specification_panel)

        result = QWidget()
        result_layout = QVBoxLayout(result)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.addWidget(self._build_metrics())

        tabs = QTabWidget()
        self.result_tabs = tabs
        self.response_plot = ResponsePlot()
        self.schematic_view = SchematicView()
        self.component_model = ComponentTableModel(self)
        self.active_rc_tab = ActiveRCTab()
        self.leapfrog_tab = LeapfrogTab()
        self.component_table = QTableView()
        self.component_table.setModel(self.component_model)
        self.component_table.setAlternatingRowColors(True)
        self.component_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.component_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.component_table.horizontalHeader().setStretchLastSection(True)
        self.component_table.verticalHeader().setVisible(False)
        tabs.addTab(self.response_plot, "Frequency Response")
        tabs.addTab(self.schematic_view, "Circuit Topology")
        tabs.addTab(self.component_table, "Components")
        tabs.addTab(self.active_rc_tab, "Fully Differential Active-RC")
        tabs.addTab(self.leapfrog_tab, "Fully Differential Leapfrog")
        result_layout.addWidget(tabs, 1)
        splitter.addWidget(result)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([350, 850])
        outer.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def _build_metrics(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.order_metric = self._metric_card("Filter Order", "—")
        self.pass_metric = self._metric_card("Worst Passband Loss", "—")
        self.stop_metric = self._metric_card("Minimum Stopband Attenuation", "—")
        layout.addWidget(self.order_metric[0])
        layout.addWidget(self.pass_metric[0])
        layout.addWidget(self.stop_metric[0])
        return container

    @staticmethod
    def _metric_card(caption: str, value: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #d7e0ea; border-radius: 7px; }"
            "QLabel { border: 0; background: transparent; }"
        )
        layout = QVBoxLayout(frame)
        caption_label = QLabel(caption)
        caption_label.setStyleSheet("color: #66788a;")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #17365d;")
        layout.addWidget(caption_label)
        layout.addWidget(value_label)
        return frame, value_label

    def _build_status_bar(self) -> None:
        status = QStatusBar()
        self.status_text = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(150)
        self.progress.hide()
        status.addWidget(self.status_text, 1)
        status.addPermanentWidget(self.progress)
        self.setStatusBar(status)

    @Slot()
    def start_design(self) -> None:
        """Validate input and begin calculation in a worker QThread."""
        if self._thread is not None:
            return
        try:
            specification = self.specification_panel.specification()
        except ValueError as error:
            self._show_error("Invalid Specification", str(error))
            return

        self._set_busy(True)
        thread = QThread(self)
        worker = DesignWorker(specification)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._apply_design)
        worker.failed.connect(lambda message: self._show_error("Synthesis Failed", message))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    @Slot(object)
    def _apply_design(self, design: Design) -> None:
        self.design = design
        self.response_plot.set_response(design.response)
        self.schematic_view.set_network(design.synthesis.network)
        self.component_model.set_network(design.synthesis.network)
        self.active_rc_tab.set_realization(design.fully_differential)
        self.leapfrog_tab.set_realization(design.leapfrog)
        self.component_table.resizeColumnsToContents()
        self.order_metric[1].setText(str(design.synthesis.order))
        self._set_metric(self.pass_metric[1], design.metrics.worst_passband_loss_db,
                         design.metrics.meets_passband)
        self._set_metric(self.stop_metric[1], design.metrics.minimum_stopband_attenuation_db,
                         design.metrics.meets_stopband)
        for action in self.export_actions:
            action.setEnabled(True)
        warnings = "  ".join(design.synthesis.warnings)
        self.status_text.setText(warnings or "Synthesis and network verification completed")
        self.design_completed.emit(design)

    @staticmethod
    def _set_metric(label: QLabel, value: float, passed: bool) -> None:
        symbol = "✓" if passed else "✗"
        color = "#08783e" if passed else "#b42318"
        label.setText(f"{value:.3f} dB  {symbol}")
        label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color};")

    @Slot()
    def _thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self.specification_panel.set_busy(busy)
        self.open_action.setDisabled(busy)
        self.save_action.setDisabled(busy)
        self.progress.setVisible(busy)
        if busy:
            self.status_text.setText("Synthesizing and calculating the frequency response…")

    @Slot()
    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Filter Project", self._dialog_directory(),
            "Open Filter Designer (*.ofd.json);;JSON (*.json)",
        )
        if not path:
            return
        try:
            project = FilterProject.load(path)
        except (OSError, ValueError) as error:
            self._show_error("Unable to Open Project", str(error))
            return
        self.project_path = Path(path)
        self.specification_panel.set_specification(project.specification)
        self.setWindowTitle(f"{project.name} — Open Filter Designer")
        self._remember_directory(path)
        self.start_design()

    @Slot()
    def save_project(self) -> None:
        try:
            specification = self.specification_panel.specification()
        except ValueError as error:
            self._show_error("Invalid Specification", str(error))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Filter Project", str(self.project_path or Path(self._dialog_directory()) / "filter.ofd.json"),
            "Open Filter Designer (*.ofd.json);;JSON (*.json)",
        )
        if not path:
            return
        project_path = Path(path)
        if not project_path.name.endswith(".ofd.json"):
            project_path = project_path.with_suffix(".ofd.json")
        try:
            FilterProject(specification, project_path.name.removesuffix(".ofd.json")).save(project_path)
        except OSError as error:
            self._show_error("Unable to Save Project", str(error))
            return
        self.project_path = project_path
        self.setWindowTitle(f"{project_path.stem} — Open Filter Designer")
        self._remember_directory(str(project_path))
        self.status_text.setText(f"Project saved: {project_path}")

    def export_design(self, kind: str) -> None:
        if self.design is None:
            return
        names = {
            "csv": ("Export Response CSV", "CSV (*.csv)", ".csv"),
            "s2p": ("Export Touchstone", "Touchstone (*.s2p)", ".s2p"),
            "cir": ("Export SPICE Netlist", "SPICE (*.cir)", ".cir"),
            "html": ("Export HTML Report", "HTML (*.html)", ".html"),
        }
        title, file_filter, extension = names[kind]
        path, _ = QFileDialog.getSaveFileName(
            self, title, str(Path(self._dialog_directory()) / f"filter{extension}"), file_filter,
        )
        if not path:
            return
        output = Path(path)
        if output.suffix.lower() != extension:
            output = output.with_suffix(extension)
        try:
            self._write_export(kind, output)
        except OSError as error:
            self._show_error("Export Failed", str(error))
            return
        self._remember_directory(str(output))
        self.status_text.setText(f"Exported: {output}")

    def _write_export(self, kind: str, output: Path) -> None:
        assert self.design is not None
        design = self.design
        if kind == "csv":
            export_csv(output, list(design.response))
        elif kind == "s2p":
            export_touchstone(
                output, list(design.response), design.specification.source_impedance_ohm
            )
        elif kind == "cir":
            sweep = suggested_sweep(design.specification)
            export_spice(output, design.synthesis.network, sweep[0], sweep[-1])
        else:
            export_html(output, design.specification, design.synthesis, design.metrics)

    @Slot()
    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Open Filter Designer",
            "<b>Open Filter Designer 0.2</b><br><br>"
            "An independently implemented passive lumped-LC filter synthesis and analysis tool.<br>"
            "The interface uses Qt for Python (PySide6) and contains no commercial software source code or assets.",
        )

    def _show_error(self, title: str, message: str) -> None:
        self.status_text.setText(message)
        QMessageBox.critical(self, title, message)

    def _dialog_directory(self) -> str:
        return str(self._settings.value("lastDirectory", str(Path.home())))

    def _remember_directory(self, path: str) -> None:
        self._settings.setValue("lastDirectory", str(Path(path).parent))

    def _restore_window_state(self) -> None:
        geometry = self._settings.value("windowGeometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Calculation in Progress", "Wait for the current filter analysis to finish before exiting.")
            event.ignore()
            return
        self._settings.setValue("windowGeometry", self.saveGeometry())
        event.accept()
