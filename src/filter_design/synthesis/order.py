"""Minimum-order calculations and normalized frequency mappings."""
from __future__ import annotations

import math
from dataclasses import dataclass

from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType


@dataclass(frozen=True, slots=True)
class FrequencyMapping:
    selectivity: float
    center_hz: float | None
    pass_bandwidth_hz: float | None


def frequency_mapping(spec: FilterSpecification) -> FrequencyMapping:
    if spec.response == ResponseType.LOWPASS:
        return FrequencyMapping(spec.stopband_hz[0] / spec.passband_hz[0], None, None)
    if spec.response == ResponseType.HIGHPASS:
        return FrequencyMapping(spec.passband_hz[0] / spec.stopband_hz[0], None, None)
    if spec.response == ResponseType.BANDPASS:
        p1, p2 = spec.passband_hz
        w0 = math.sqrt(p1 * p2)
        bandwidth = p2 - p1
        mapped = [abs((s * s - w0 * w0) / (bandwidth * s)) for s in spec.stopband_hz]
        return FrequencyMapping(min(mapped), w0, bandwidth)
    p1, p2 = spec.passband_hz
    s1, s2 = spec.stopband_hz
    w0 = math.sqrt(s1 * s2)
    stop_bandwidth = s2 - s1
    pass_mapping = [stop_bandwidth * p / abs(p * p - w0 * w0) for p in (p1, p2)]
    limiting_pass = max(pass_mapping)
    return FrequencyMapping(1 / limiting_pass, w0, stop_bandwidth / limiting_pass)


def minimum_order(spec: FilterSpecification) -> int:
    mapping = frequency_mapping(spec)
    if mapping.selectivity <= 1:
        raise ValueError("Frequency edges do not provide realizable selectivity")
    ep2 = 10 ** (spec.passband_ripple_db / 10) - 1
    ratio = (10 ** (spec.stopband_attenuation_db / 10) - 1) / ep2
    if spec.approximation == Approximation.BUTTERWORTH:
        value = math.log10(ratio) / (2 * math.log10(mapping.selectivity))
    else:
        value = math.acosh(math.sqrt(ratio)) / math.acosh(mapping.selectivity)
    return max(1, math.ceil(value - 1e-12))
