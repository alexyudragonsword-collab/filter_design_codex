"""Specification-oriented measurements from a sampled response."""
from __future__ import annotations

from dataclasses import dataclass

from filter_design.domain.specifications import FilterSpecification, ResponseType
from .response import ResponsePoint


@dataclass(frozen=True, slots=True)
class ResponseMetrics:
    worst_passband_loss_db: float
    minimum_stopband_attenuation_db: float
    maximum_return_loss_db: float
    meets_passband: bool
    meets_stopband: bool


def measure(spec: FilterSpecification, response: list[ResponsePoint]) -> ResponseMetrics:
    if spec.response == ResponseType.LOWPASS:
        pass_points = [p for p in response if p.frequency_hz <= spec.passband_hz[0]]
        stop_points = [p for p in response if p.frequency_hz >= spec.stopband_hz[0]]
    elif spec.response == ResponseType.HIGHPASS:
        pass_points = [p for p in response if p.frequency_hz >= spec.passband_hz[0]]
        stop_points = [p for p in response if p.frequency_hz <= spec.stopband_hz[0]]
    elif spec.response == ResponseType.BANDPASS:
        p1, p2 = spec.passband_hz; s1, s2 = spec.stopband_hz
        pass_points = [p for p in response if p1 <= p.frequency_hz <= p2]
        stop_points = [p for p in response if p.frequency_hz <= s1 or p.frequency_hz >= s2]
    else:
        p1, p2 = spec.passband_hz; s1, s2 = spec.stopband_hz
        pass_points = [p for p in response if p.frequency_hz <= p1 or p.frequency_hz >= p2]
        stop_points = [p for p in response if s1 <= p.frequency_hz <= s2]
    if not pass_points or not stop_points:
        raise ValueError("Sweep does not cover both passband and stopband")
    worst_pass = max(p.insertion_loss_db for p in pass_points)
    minimum_stop = min(p.insertion_loss_db for p in stop_points)
    maximum_return = max(p.return_loss_db for p in pass_points)
    return ResponseMetrics(worst_pass, minimum_stop, maximum_return,
                           worst_pass <= spec.passband_ripple_db + 0.05,
                           minimum_stop >= spec.stopband_attenuation_db - 0.05)
