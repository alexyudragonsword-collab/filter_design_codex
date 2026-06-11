"""Read-only Qt table model for synthesized components."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from filter_design.domain.network import Branch, LadderNetwork
from filter_design.formatting import engineering


class ComponentTableModel(QAbstractTableModel):
    HEADERS = ("编号", "元件", "位置", "谐振连接", "数值")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[Branch, object]] = []

    def set_network(self, network: LadderNetwork | None) -> None:
        self.beginResetModel()
        self._rows = [] if network is None else [
            (branch, component)
            for branch in network.branches
            for component in branch.components
        ]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 - Qt API
        return 0 if parent.isValid() else len(self._rows)

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
        branch, component = self._rows[index.row()]
        values = (
            component.reference,
            "电感" if component.kind.value == "L" else "电容",
            "串联支路" if branch.position.value == "series" else "并联支路",
            "串联" if branch.connection.value == "series" else "并联",
            engineering(component.value, component.unit),
        )
        return values[index.column()]
