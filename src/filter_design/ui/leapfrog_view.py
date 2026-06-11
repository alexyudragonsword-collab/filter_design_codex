"""Signal-flow renderer for a fully differential leapfrog filter."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from filter_design.domain.leapfrog import LeapfrogRealization


class LeapfrogView(QWidget):
    """Draw interleaved differential integrators and adjacent-state feedback."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._realization: LeapfrogRealization | None = None
        self.setMinimumHeight(250)

    def set_realization(self, realization: LeapfrogRealization | None) -> None:
        self._realization = realization
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if self._realization is None:
            painter.setPen(QColor("#778899"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Synthesize a design first")
            return
        if not self._realization.supported:
            painter.setPen(QColor("#b42318"))
            painter.drawText(
                self.rect().adjusted(30, 30, -30, -30),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._realization.diagnostic,
            )
            return

        states = self._realization.states
        state_width = max(112.0, (self.width() - 120.0) / max(len(states), 1))
        required = 95.0 + state_width * len(states)
        scale = min(1.0, self.width() / required)
        painter.scale(scale, scale)
        y = 115.0
        x = 65.0
        painter.setPen(QPen(QColor("#26384a"), 2))
        painter.drawText(QPointF(12, y + 5), "VIN±")
        painter.drawLine(QPointF(48, y), QPointF(x, y))

        centers: list[QPointF] = []
        for state in states:
            box = QRectF(x + 8, y - 38, state_width - 16, 76)
            painter.setBrush(QColor("#e8f3fa"))
            painter.setPen(QPen(QColor("#1677b8"), 2))
            painter.drawRoundedRect(box, 7, 7)
            painter.setPen(QColor("#17365d"))
            painter.drawText(
                box, Qt.AlignmentFlag.AlignCenter,
                f"{state.reference}±\nIdeal op-amp integrator\n{state.source_component}",
            )
            painter.setPen(QPen(QColor("#26384a"), 2))
            painter.drawLine(QPointF(x, y), QPointF(x + 8, y))
            painter.drawLine(QPointF(x + state_width - 8, y), QPointF(x + state_width, y))
            centers.append(box.center())
            x += state_width

        painter.drawText(QPointF(x + 2, y - 12), "VOUT±")
        painter.setPen(QPen(QColor("#e07a1f"), 1.5, Qt.PenStyle.DashLine))
        for index in range(len(centers) - 1):
            left, right = centers[index], centers[index + 1]
            upper = 45.0 if index % 2 == 0 else 185.0
            painter.drawPolyline([
                QPointF(right.x(), right.y() - 38 if upper < y else right.y() + 38),
                QPointF(right.x(), upper),
                QPointF(left.x(), upper),
                QPointF(left.x(), left.y() - 38 if upper < y else left.y() + 38),
            ])
        painter.setPen(QColor("#66788a"))
        painter.drawText(
            QRectF(55, 210, required - 90, 28), Qt.AlignmentFlag.AlignCenter,
            "Adjacent-state resistor pairs reproduce the passive LC ladder signal flow; "
            "cross-coupling sets positive signs and same-side routing sets negative signs.",
        )
