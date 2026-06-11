"""Composite tab for fully differential active-RC topology and values."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from filter_design.domain.active_rc import FullyDifferentialRealization

from .active_rc_model import ActiveRCComponentModel
from .active_rc_view import ActiveRCTopologyView


class ActiveRCTab(QWidget):
    """Present the op-amp-RC realization assumptions, topology, and BOM."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.summary = QLabel(
            "Ideal fully differential realization: capacitors are split symmetrically and "
            "inductors are replaced by mirrored Antoniou GIC cells referenced to VCM."
        )
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            "background: #eef6fb; border: 1px solid #c9deed; border-radius: 6px; "
            "padding: 9px; color: #23445f;"
        )
        layout.addWidget(self.summary)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.topology = ActiveRCTopologyView()
        self.model = ActiveRCComponentModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        splitter.addWidget(self.topology)
        splitter.addWidget(self.table)
        splitter.setSizes([290, 300])
        layout.addWidget(splitter, 1)

        footnote = QLabel(
            "GIC equation for equal resistors: L = C × R². Values assume ideal op-amps; "
            "select amplifiers with sufficient gain-bandwidth, slew rate, noise, output drive, "
            "and common-mode range before hardware implementation."
        )
        footnote.setWordWrap(True)
        footnote.setStyleSheet("color: #66788a; padding: 4px 2px;")
        layout.addWidget(footnote)

    def set_realization(self, realization: FullyDifferentialRealization | None) -> None:
        self.topology.set_realization(realization)
        self.model.set_realization(realization)
        self.table.resizeColumnsToContents()
        if realization is not None:
            self.summary.setText(
                "Fully differential active-RC realization: "
                f"{realization.op_amp_count} op-amps, {realization.resistor_count} resistors, "
                f"and {realization.capacitor_count} capacitors. The two signal legs are "
                f"symmetric around {realization.common_mode_label}."
            )
