"""Qt schematic renderer for synthesized ladder networks."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from filter_design.domain.network import BranchPosition, LadderNetwork


class SchematicView(QWidget):
    """Displays the generated ladder topology without a scene dependency."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._network: LadderNetwork | None = None
        self.setMinimumSize(560, 300)

    def set_network(self, network: LadderNetwork | None) -> None:
        self._network = network
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if not self._network:
            painter.setPen(QColor("#778899"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "综合后显示 LC 梯形网络")
            return

        branches = self._network.branches
        width = max(self.width() - 100.0, 100.0)
        spacing = max(92.0, width / max(len(branches), 1))
        required = 100 + spacing * len(branches)
        scale = min(1.0, self.width() / required)
        painter.scale(scale, scale)
        center_y = self.height() / (2 * scale) - 25
        x = 50.0
        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(18, center_y), QPointF(x, center_y))
        painter.drawText(QPointF(18, center_y - 14), "输入")

        for branch in branches:
            label = " / ".join(component.reference for component in branch.components)
            if branch.position == BranchPosition.SERIES:
                self._draw_series(painter, x, center_y, spacing, label)
            else:
                painter.drawLine(QPointF(x, center_y), QPointF(x + spacing, center_y))
                self._draw_shunt(painter, x + spacing / 2, center_y, label)
            x += spacing

        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(x, center_y), QPointF(x + 35, center_y))
        painter.drawText(QPointF(x + 3, center_y - 14), "输出")

    @staticmethod
    def _draw_series(painter: QPainter, x: float, y: float,
                     spacing: float, label: str) -> None:
        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(x, y), QPointF(x + 13, y))
        body = QRectF(x + 13, y - 20, spacing - 26, 40)
        painter.setBrush(QColor("#e8f3fa"))
        painter.setPen(QPen(QColor("#1677b8"), 2))
        painter.drawRoundedRect(body, 5, 5)
        painter.setPen(QColor("#17365d"))
        painter.drawText(body, Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(x + spacing - 13, y), QPointF(x + spacing, y))

    @staticmethod
    def _draw_shunt(painter: QPainter, x: float, y: float, label: str) -> None:
        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(x, y), QPointF(x, y + 28))
        body = QRectF(x - 34, y + 28, 68, 42)
        painter.setBrush(QColor("#fff1e5"))
        painter.setPen(QPen(QColor("#e07a1f"), 2))
        painter.drawRoundedRect(body, 5, 5)
        painter.setPen(QColor("#6d3a0c"))
        painter.drawText(body, Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(QPen(QColor("#27384a"), 2))
        painter.drawLine(QPointF(x, y + 70), QPointF(x, y + 88))
        painter.drawLine(QPointF(x - 18, y + 88), QPointF(x + 18, y + 88))
        painter.drawLine(QPointF(x - 12, y + 94), QPointF(x + 12, y + 94))
        painter.drawLine(QPointF(x - 6, y + 100), QPointF(x + 6, y + 100))
