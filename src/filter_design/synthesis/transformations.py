"""Scale normalized ladder coefficients into physical LC networks."""
from __future__ import annotations

import math

from filter_design.domain.network import (Branch, BranchPosition, Component,
    ComponentKind, Connection, LadderNetwork)
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from .order import frequency_mapping


def _component(kind: ComponentKind, value: float, counters: dict[str, int]) -> Component:
    counters[kind.value] += 1
    return Component(kind, value, f"{kind.value}{counters[kind.value]}")


def transform_ladder(spec: FilterSpecification, g: tuple[float, ...], order: int) -> LadderNetwork:
    r0 = spec.source_impedance_ohm
    counters = {"L": 0, "C": 0}
    branches: list[Branch] = []
    mapping = frequency_mapping(spec)
    epsilon = math.sqrt(10 ** (spec.passband_ripple_db / 10) - 1)
    butter_scale = epsilon ** (-1 / order) if spec.approximation == Approximation.BUTTERWORTH else 1.0

    if spec.response == ResponseType.LOWPASS:
        wc = 2 * math.pi * spec.passband_hz[0] * butter_scale
    elif spec.response == ResponseType.HIGHPASS:
        wc = 2 * math.pi * spec.passband_hz[0] / butter_scale
    else:
        w0 = 2 * math.pi * mapping.center_hz
        bandwidth = 2 * math.pi * mapping.pass_bandwidth_hz * (1 / butter_scale if spec.response == ResponseType.BANDSTOP else butter_scale)

    for index, coefficient in enumerate(g[1:-1], start=1):
        series = index % 2 == 1
        position = BranchPosition.SERIES if series else BranchPosition.SHUNT
        if spec.response == ResponseType.LOWPASS:
            if series:
                parts = (_component(ComponentKind.INDUCTOR, r0 * coefficient / wc, counters),)
            else:
                parts = (_component(ComponentKind.CAPACITOR, coefficient / (r0 * wc), counters),)
            connection = Connection.SERIES
        elif spec.response == ResponseType.HIGHPASS:
            if series:
                parts = (_component(ComponentKind.CAPACITOR, 1 / (r0 * wc * coefficient), counters),)
            else:
                parts = (_component(ComponentKind.INDUCTOR, r0 / (wc * coefficient), counters),)
            connection = Connection.SERIES
        elif spec.response == ResponseType.BANDPASS:
            if series:
                inductance = r0 * coefficient / bandwidth
                capacitance = bandwidth / (r0 * coefficient * w0 * w0)
                parts = (_component(ComponentKind.INDUCTOR, inductance, counters),
                         _component(ComponentKind.CAPACITOR, capacitance, counters))
                connection = Connection.SERIES
            else:
                capacitance = coefficient / (r0 * bandwidth)
                inductance = r0 * bandwidth / (coefficient * w0 * w0)
                parts = (_component(ComponentKind.INDUCTOR, inductance, counters),
                         _component(ComponentKind.CAPACITOR, capacitance, counters))
                connection = Connection.PARALLEL
        else:  # band stop
            if series:
                inductance = r0 * coefficient * bandwidth / (w0 * w0)
                capacitance = 1 / (r0 * coefficient * bandwidth)
                parts = (_component(ComponentKind.INDUCTOR, inductance, counters),
                         _component(ComponentKind.CAPACITOR, capacitance, counters))
                connection = Connection.PARALLEL
            else:
                inductance = r0 / (coefficient * bandwidth)
                capacitance = coefficient * bandwidth / (r0 * w0 * w0)
                parts = (_component(ComponentKind.INDUCTOR, inductance, counters),
                         _component(ComponentKind.CAPACITOR, capacitance, counters))
                connection = Connection.SERIES
        branches.append(Branch(position, connection, parts))
    return LadderNetwork(tuple(branches), r0, spec.load_impedance_ohm)
