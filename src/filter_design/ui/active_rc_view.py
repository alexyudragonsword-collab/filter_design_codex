"""Topology view for the fully differential op-amp-RC realization."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from filter_design.domain.active_rc import ActiveRCBranch, FullyDifferentialRealization
from filter_design.domain.network import BranchPosition, Connection


class ActiveRCTopologyView(QWidget):
    """Render mirrored positive/negative branches around a common-mode rail."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._realization: FullyDifferentialRealization | None = None
        self.setMinimumHeight(255)

    def set_realization(self, realization: FullyDifferentialRealization | None) -> None:
        self._realization = realization
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if not self._realization:
            painter.setPen(QColor("#778899"))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "The fully differential active-RC realization will appear after synthesis",
            )
            return

        branches = self._realization.branches
        available_width = max(self.width() - 130.0, 200.0)
        branch_width = max(115.0, available_width / max(len(branches), 1))
        required_width = 105.0 + branch_width * len(branches)
        scale = min(1.0, self.width() / required_width)
        painter.scale(scale, scale)

        plus_y, vcm_y, minus_y = 68.0, 130.0, 192.0
        x = 70.0
        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawText(QPointF(12, plus_y + 5), "IN+")
        painter.drawText(QPointF(12, minus_y + 5), "IN-")
        painter.drawLine(QPointF(50, plus_y), QPointF(x, plus_y))
        painter.drawLine(QPointF(50, minus_y), QPointF(x, minus_y))
        painter.setPen(QPen(QColor("#8a9aaa"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(50, vcm_y), QPointF(required_width - 20, vcm_y))
        painter.drawText(QPointF(12, vcm_y + 5), "VCM")

        for branch in branches:
            self._draw_branch(painter, branch, x, plus_y, minus_y, vcm_y, branch_width)
            x += branch_width

        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawLine(QPointF(x, plus_y), QPointF(x + 35, plus_y))
        painter.drawLine(QPointF(x, minus_y), QPointF(x + 35, minus_y))
        painter.drawText(QPointF(x + 4, plus_y - 12), "OUT+")
        painter.drawText(QPointF(x + 4, minus_y - 12), "OUT-")

    def _draw_branch(self, painter: QPainter, branch: ActiveRCBranch, x: float,
                     plus_y: float, minus_y: float, vcm_y: float,
                     width: float) -> None:
        positive = self._branch_label(branch, positive=True)
        negative = self._branch_label(branch, positive=False)
        connection = "series" if branch.connection == Connection.SERIES else "parallel"
        painter.setPen(QColor("#5f6f80"))
        painter.drawText(
            QRectF(x, 10, width, 24), Qt.AlignmentFlag.AlignCenter,
            f"{branch.reference} · {branch.position.value} · {connection}",
        )
        if branch.position == BranchPosition.SERIES:
            self._draw_series_cell(painter, x, plus_y, width, positive)
            self._draw_series_cell(painter, x, minus_y, width, negative)
        else:
            painter.setPen(QPen(QColor("#26384a"), 2))
            painter.drawLine(QPointF(x, plus_y), QPointF(x + width, plus_y))
            painter.drawLine(QPointF(x, minus_y), QPointF(x + width, minus_y))
            center = x + width / 2
            self._draw_shunt_cell(painter, center, plus_y, vcm_y, positive, downward=True)
            self._draw_shunt_cell(painter, center, minus_y, vcm_y, negative, downward=False)

    @staticmethod
    def _branch_label(branch: ActiveRCBranch, *, positive: bool) -> str:
        labels = [stage.positive_label if positive else stage.negative_label for stage in branch.stages]
        separator = " + " if branch.connection == Connection.SERIES else " || "
        return separator.join(labels)

    @staticmethod
    def _draw_series_cell(painter: QPainter, x: float, y: float,
                          width: float, label: str) -> None:
        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawLine(QPointF(x, y), QPointF(x + 10, y))
        box = QRectF(x + 10, y - 22, width - 20, 44)
        painter.setBrush(QColor("#e8f3fa"))
        painter.setPen(QPen(QColor("#1677b8"), 2))
        painter.drawRoundedRect(box, 6, 6)
        painter.setPen(QColor("#17365d"))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawLine(QPointF(x + width - 10, y), QPointF(x + width, y))

    @staticmethod
    def _draw_shunt_cell(painter: QPainter, x: float, rail_y: float,
                         vcm_y: float, label: str, *, downward: bool) -> None:
        box_height = 38.0
        top = rail_y + 8 if downward else rail_y - 8 - box_height
        box = QRectF(x - 42, top, 84, box_height)
        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawLine(
            QPointF(x, rail_y),
            QPointF(x, box.top() if downward else box.bottom()),
        )
        painter.setBrush(QColor("#fff1e5"))
        painter.setPen(QPen(QColor("#e07a1f"), 2))
        painter.drawRoundedRect(box, 6, 6)
        painter.setPen(QColor("#6d3a0c"))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(QPen(QColor("#8a9aaa"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(
            QPointF(x, box.bottom() if downward else box.top()),
            QPointF(x, vcm_y),
        )
