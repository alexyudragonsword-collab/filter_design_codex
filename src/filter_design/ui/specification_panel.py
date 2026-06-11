"""Qt editor for validated filter specifications."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType


class SpecificationPanel(QWidget):
    """Collects engineering-unit input and emits synthesis requests."""

    design_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("设计指标")
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.response = QComboBox()
        self.response.addItem("低通", ResponseType.LOWPASS)
        self.response.addItem("高通", ResponseType.HIGHPASS)
        self.response.addItem("带通", ResponseType.BANDPASS)
        self.response.addItem("带阻", ResponseType.BANDSTOP)
        self.approximation = QComboBox()
        self.approximation.addItem("Butterworth（最大平坦）", Approximation.BUTTERWORTH)
        self.approximation.addItem("Chebyshev I（等纹波）", Approximation.CHEBYSHEV1)

        self.pass1 = self._frequency_spin(1.0)
        self.pass2 = self._frequency_spin(2.0)
        self.stop1 = self._frequency_spin(2.0)
        self.stop2 = self._frequency_spin(3.0)
        self.ripple = self._numeric_spin(0.001, 20.0, 0.5, " dB", 3)
        self.attenuation = self._numeric_spin(0.1, 300.0, 40.0, " dB", 2)
        self.impedance = self._numeric_spin(0.01, 1_000_000.0, 50.0, " Ω", 3)
        self.order = QSpinBox()
        self.order.setRange(0, 30)
        self.order.setSpecialValueText("自动")
        self.order.setValue(0)

        form.addRow("响应类型", self.response)
        form.addRow("逼近函数", self.approximation)
        form.addRow("通带边缘 1", self.pass1)
        form.addRow("通带边缘 2", self.pass2)
        form.addRow("阻带边缘 1", self.stop1)
        form.addRow("阻带边缘 2", self.stop2)
        form.addRow("通带纹波/衰减", self.ripple)
        form.addRow("最小阻带衰减", self.attenuation)
        form.addRow("端口阻抗", self.impedance)
        form.addRow("滤波器阶数", self.order)
        layout.addWidget(group)

        self.design_button = QPushButton("综合并分析")
        self.design_button.setObjectName("PrimaryButton")
        self.design_button.clicked.connect(self.design_requested)
        layout.addWidget(self.design_button)

        note = QLabel("当前综合使用理想无损 LC 元件。制造前应校验元件 Q 值、寄生参数、容差、功率和布局。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #66788a; padding: 8px 2px;")
        layout.addWidget(note)
        layout.addStretch(1)

        self.response.currentIndexChanged.connect(self._response_changed)
        self._response_changed(set_defaults=False)

    @staticmethod
    def _frequency_spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.000001, 1_000_000_000.0)
        spin.setDecimals(6)
        spin.setValue(value)
        spin.setSuffix(" MHz")
        spin.setSingleStep(0.1)
        return spin

    @staticmethod
    def _numeric_spin(minimum: float, maximum: float, value: float,
                      suffix: str, decimals: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setSuffix(suffix)
        return spin

    def _response_changed(self, _index: int = -1, *, set_defaults: bool = True) -> None:
        response = self.response.currentData()
        band = response in (ResponseType.BANDPASS, ResponseType.BANDSTOP)
        self.pass2.setEnabled(band)
        self.stop2.setEnabled(band)
        if set_defaults:
            defaults = {
                ResponseType.LOWPASS: (1.0, 2.0, 2.0, 3.0),
                ResponseType.HIGHPASS: (2.0, 3.0, 1.0, 2.0),
                ResponseType.BANDPASS: (1.0, 2.0, 0.7, 2.5),
                ResponseType.BANDSTOP: (0.7, 2.5, 1.0, 2.0),
            }[response]
            for widget, value in zip(
                (self.pass1, self.pass2, self.stop1, self.stop2), defaults, strict=True
            ):
                widget.setValue(value)

    def specification(self) -> FilterSpecification:
        """Build the domain specification from current widget values."""
        response = ResponseType(self.response.currentData())
        passband = (self.pass1.value() * 1e6,)
        stopband = (self.stop1.value() * 1e6,)
        if response in (ResponseType.BANDPASS, ResponseType.BANDSTOP):
            passband += (self.pass2.value() * 1e6,)
            stopband += (self.stop2.value() * 1e6,)
        return FilterSpecification(
            response=response,
            approximation=Approximation(self.approximation.currentData()),
            passband_hz=passband,
            stopband_hz=stopband,
            passband_ripple_db=self.ripple.value(),
            stopband_attenuation_db=self.attenuation.value(),
            source_impedance_ohm=self.impedance.value(),
            load_impedance_ohm=self.impedance.value(),
            order=self.order.value() or None,
        )

    def set_specification(self, specification: FilterSpecification) -> None:
        """Populate widgets from a loaded project without changing domain data."""
        self._set_combo_data(self.response, specification.response)
        self._set_combo_data(self.approximation, specification.approximation)
        self.pass1.setValue(specification.passband_hz[0] / 1e6)
        self.stop1.setValue(specification.stopband_hz[0] / 1e6)
        if len(specification.passband_hz) == 2:
            self.pass2.setValue(specification.passband_hz[1] / 1e6)
            self.stop2.setValue(specification.stopband_hz[1] / 1e6)
        self.ripple.setValue(specification.passband_ripple_db)
        self.attenuation.setValue(specification.stopband_attenuation_db)
        self.impedance.setValue(specification.source_impedance_ohm)
        self.order.setValue(specification.order or 0)
        self._response_changed(set_defaults=False)

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def set_busy(self, busy: bool) -> None:
        self.design_button.setDisabled(busy)
        self.design_button.setText("正在计算…" if busy else "综合并分析")
