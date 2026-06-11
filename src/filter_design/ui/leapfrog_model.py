"""Qt table models for leapfrog state equations and physical components."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from filter_design.domain.leapfrog import LeapfrogRealization
from filter_design.formatting import engineering


class LeapfrogStateModel(QAbstractTableModel):
    HEADERS = ("State", "LC Variable", "State Equation", "Integrator C")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._states = ()

    def set_realization(self, realization: LeapfrogRealization | None) -> None:
        self.beginResetModel()
        self._states = () if realization is None or not realization.supported else realization.states
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._states)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (
            Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.TextAlignmentRole
        ):
            return None
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        state = self._states[index.row()]
        values = (
            state.reference,
            f"{state.source_component}: {state.variable}",
            state.equation,
            engineering(state.integrating_capacitance_f, "F"),
        )
        return values[index.column()]


class LeapfrogComponentModel(QAbstractTableModel):
    HEADERS = ("Reference", "Type", "State", "Side", "Function", "Value")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._components = ()

    def set_realization(self, realization: LeapfrogRealization | None) -> None:
        self.beginResetModel()
        self._components = (
            () if realization is None or not realization.supported else realization.components
        )
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._components)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (
            Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.TextAlignmentRole
        ):
            return None
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        component = self._components[index.row()]
        values = (
            component.reference,
            "Resistor" if component.kind.value == "R" else "Capacitor",
            component.state,
            component.side,
            component.function,
            engineering(component.value, component.unit),
        )
        return values[index.column()]
