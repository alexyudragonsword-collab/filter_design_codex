"""Composite Qt tab for the ideal fully differential leapfrog realization."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QTabWidget, QTableView, QVBoxLayout, QWidget

from filter_design.domain.leapfrog import LeapfrogRealization

from .leapfrog_model import LeapfrogComponentModel, LeapfrogStateModel
from .leapfrog_view import LeapfrogView


class LeapfrogTab(QWidget):
    """Show leapfrog signal flow, state equations, and the complete RC BOM."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.summary = QLabel(
            "Exact low-pass LC leapfrog simulation using ideal fully differential integrators."
        )
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            "background: #eef6fb; border: 1px solid #c9deed; border-radius: 6px; "
            "padding: 9px; color: #23445f;"
        )
        layout.addWidget(self.summary)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.flow_view = LeapfrogView()
        details = QTabWidget()
        self.details_tabs = details
        self.state_model = LeapfrogStateModel(self)
        self.component_model = LeapfrogComponentModel(self)
        self.state_table = self._table(self.state_model)
        self.component_table = self._table(self.component_model)
        details.addTab(self.state_table, "State Equations")
        details.addTab(self.component_table, "Resistor and Capacitor Values")
        splitter.addWidget(self.flow_view)
        splitter.addWidget(details)
        splitter.setSizes([285, 310])
        layout.addWidget(splitter, 1)

        note = QLabel(
            "Ideal-op-amp assumption: infinite gain, bandwidth, input impedance, slew rate, "
            "and output drive, with zero offset and noise. Positive state coefficients use "
            "cross-coupled resistor pairs; negative coefficients use same-side pairs."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #66788a; padding: 4px 2px;")
        layout.addWidget(note)

    @staticmethod
    def _table(model) -> QTableView:
        table = QTableView()
        table.setModel(model)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        return table

    def set_realization(self, realization: LeapfrogRealization | None) -> None:
        self.flow_view.set_realization(realization)
        self.state_model.set_realization(realization)
        self.component_model.set_realization(realization)
        self.state_table.resizeColumnsToContents()
        self.component_table.resizeColumnsToContents()
        if realization is None:
            return
        if realization.supported:
            self.summary.setStyleSheet(
                "background: #eef6fb; border: 1px solid #c9deed; border-radius: 6px; "
                "padding: 9px; color: #23445f;"
            )
            self.summary.setText(
                "Fully differential leapfrog realization: "
                f"{len(realization.states)} integrator states, {realization.op_amp_count} ideal "
                f"op-amps, {realization.resistor_count} resistors, and "
                f"{realization.capacitor_count} capacitors. Output is "
                f"{realization.output_gain:g} × {realization.output_state}."
            )
        else:
            self.summary.setStyleSheet(
                "background: #fff1f0; border: 1px solid #f1b8b3; border-radius: 6px; "
                "padding: 9px; color: #8f1d18;"
            )
            self.summary.setText(realization.diagnostic)
