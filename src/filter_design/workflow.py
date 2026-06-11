"""High-level workflow kept independent from command-line and desktop UIs."""
from __future__ import annotations

from dataclasses import dataclass

from filter_design.analysis.metrics import ResponseMetrics, measure
from filter_design.analysis.response import ResponsePoint, analyze, logarithmic_sweep
from filter_design.domain.active_rc import FullyDifferentialRealization
from filter_design.domain.leapfrog import LeapfrogRealization
from filter_design.domain.network import SynthesisResult
from filter_design.domain.specifications import FilterSpecification
from filter_design.realization.fully_differential import realize_fully_differential
from filter_design.realization.leapfrog import realize_fully_differential_leapfrog
from filter_design.synthesis.service import synthesize_filter


@dataclass(frozen=True, slots=True)
class Design:
    specification: FilterSpecification
    synthesis: SynthesisResult
    response: tuple[ResponsePoint, ...]
    metrics: ResponseMetrics
    fully_differential: FullyDifferentialRealization
    leapfrog: LeapfrogRealization


def suggested_sweep(spec: FilterSpecification, points: int = 701) -> list[float]:
    edges = (*spec.passband_hz, *spec.stopband_hz)
    return logarithmic_sweep(min(edges) / 10, max(edges) * 10, points)


def design_filter(specification: FilterSpecification, points: int = 701) -> Design:
    synthesis = synthesize_filter(specification)
    response = analyze(synthesis.network, suggested_sweep(specification, points))
    metrics = measure(specification, response)
    fully_differential = realize_fully_differential(synthesis.network)
    leapfrog = realize_fully_differential_leapfrog(specification, synthesis.network)
    return Design(
        specification, synthesis, tuple(response), metrics, fully_differential, leapfrog
    )
