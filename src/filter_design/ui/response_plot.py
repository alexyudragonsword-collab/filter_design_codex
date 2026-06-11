"""Dependency-free Qt response plot for sampled S-parameter data."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from filter_design.analysis.response import ResponsePoint
from filter_design.formatting import engineering


class ResponsePlot(QWidget):
    """Paint insertion and return loss on a logarithmic frequency axis."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._response: tuple[ResponsePoint, ...] = ()
        self.setMinimumSize(560, 340)
        self.setToolTip("蓝色：S21 插入损耗；橙色：S11 回波损耗")

    def set_response(self, response: tuple[ResponsePoint, ...]) -> None:
        self._response = response
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        chart = QRectF(72, 28, max(10, self.width() - 100), max(10, self.height() - 90))
        self._draw_grid(painter, chart)
        if len(self._response) < 2:
            painter.setPen(QColor("#778899"))
            painter.drawText(chart, Qt.AlignmentFlag.AlignCenter, "综合后显示频率响应")
            return

        minimum = math.log10(self._response[0].frequency_hz)
        maximum = math.log10(self._response[-1].frequency_hz)
        maximum_db = self._y_max()
        self._draw_curve(painter, chart, minimum, maximum, maximum_db,
                         "insertion_loss_db", QColor("#1677b8"))
        self._draw_curve(painter, chart, minimum, maximum, maximum_db,
                         "return_loss_db", QColor("#e07a1f"))
        self._draw_labels(painter, chart, maximum_db)

    def _y_max(self) -> float:
        values = [min(point.insertion_loss_db, 160.0) for point in self._response]
        values.extend(min(point.return_loss_db, 160.0) for point in self._response)
        peak = max(values, default=80.0)
        return max(40.0, min(160.0, math.ceil(peak / 20.0) * 20.0))

    @staticmethod
    def _draw_grid(painter: QPainter, chart: QRectF) -> None:
        painter.setPen(QPen(QColor("#dfe7ef"), 1))
        for index in range(5):
            y = chart.top() + chart.height() * index / 4
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
        for index in range(7):
            x = chart.left() + chart.width() * index / 6
            painter.drawLine(QPointF(x, chart.top()), QPointF(x, chart.bottom()))
        painter.setPen(QPen(QColor("#9fb0c0"), 1))
        painter.drawRect(chart)

    def _draw_curve(self, painter: QPainter, chart: QRectF, minimum: float,
                    maximum: float, maximum_db: float, attribute: str,
                    color: QColor) -> None:
        path = QPainterPath()
        for index, point in enumerate(self._response):
            x = chart.left() + (
                (math.log10(point.frequency_hz) - minimum) / (maximum - minimum)
            ) * chart.width()
            value = min(max(getattr(point, attribute), 0.0), maximum_db)
            y = chart.top() + value / maximum_db * chart.height()
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(color, 2.2))
        painter.drawPath(path)

    def _draw_labels(self, painter: QPainter, chart: QRectF, maximum_db: float) -> None:
        painter.setPen(QColor("#526477"))
        metrics = QFontMetrics(painter.font())
        for index in range(5):
            value = maximum_db * index / 4
            y = chart.top() + chart.height() * index / 4
            text = f"{value:.0f}"
            painter.drawText(QRectF(10, y - 9, chart.left() - 18, 18),
                             Qt.AlignmentFlag.AlignRight, text)
        painter.drawText(QRectF(8, chart.top(), 20, chart.height()),
                         Qt.AlignmentFlag.AlignVCenter, "dB")
        first = engineering(self._response[0].frequency_hz, "Hz")
        last = engineering(self._response[-1].frequency_hz, "Hz")
        painter.drawText(QPointF(chart.left(), chart.bottom() + 25), first)
        painter.drawText(QPointF(chart.right() - metrics.horizontalAdvance(last),
                                 chart.bottom() + 25), last)
        painter.setPen(QPen(QColor("#1677b8"), 2))
        painter.drawLine(QPointF(chart.left() + 10, chart.top() + 14),
                         QPointF(chart.left() + 36, chart.top() + 14))
        painter.setPen(QColor("#1677b8"))
        painter.drawText(QPointF(chart.left() + 43, chart.top() + 18), "S21 插入损耗")
        painter.setPen(QPen(QColor("#e07a1f"), 2))
        painter.drawLine(QPointF(chart.left() + 155, chart.top() + 14),
                         QPointF(chart.left() + 181, chart.top() + 14))
        painter.setPen(QColor("#e07a1f"))
        painter.drawText(QPointF(chart.left() + 188, chart.top() + 18), "S11 回波损耗")
