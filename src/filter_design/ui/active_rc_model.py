"""Qt table model for fully differential active-RC components."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from filter_design.domain.active_rc import FullyDifferentialRealization
from filter_design.formatting import engineering


class ActiveRCComponentModel(QAbstractTableModel):
    HEADERS = ("Reference", "Type", "Stage", "Side", "Function", "Value")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._components = ()

    def set_realization(self, realization: FullyDifferentialRealization | None) -> None:
        self.beginResetModel()
        self._components = () if realization is None else realization.components
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self._components)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.TextAlignmentRole,
        ):
            return None
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        component = self._components[index.row()]
        values = (
            component.reference,
            "Resistor" if component.kind.value == "R" else "Capacitor",
            component.stage,
            component.side,
            component.function,
            engineering(component.value, component.unit),
        )
        return values[index.column()]
