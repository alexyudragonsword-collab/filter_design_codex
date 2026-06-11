"""Application-facing synthesis entry point."""
from __future__ import annotations

from filter_design.domain.network import SynthesisResult
from filter_design.domain.specifications import Approximation, FilterSpecification
from .order import minimum_order
from .prototypes import prototype_g
from .transformations import transform_ladder


def synthesize_filter(specification: FilterSpecification) -> SynthesisResult:
    calculated_order = minimum_order(specification)
    order = specification.order or calculated_order
    warnings: list[str] = []
    if specification.order is None and specification.approximation == Approximation.CHEBYSHEV1 and order % 2 == 0:
        order += 1
        warnings.append("Order promoted to the next odd value for an equal-termination Chebyshev ladder.")
    g = prototype_g(specification.approximation, order,
                    specification.passband_ripple_db)
    network = transform_ladder(specification, g, order)
    if specification.source_impedance_ohm != specification.load_impedance_ohm:
        warnings.append("Prototype synthesis assumes equal terminations; response includes the requested mismatch.")
    if specification.order is not None and specification.order < calculated_order:
        warnings.append("The fixed order is below the calculated minimum and may not meet specifications.")
    return SynthesisResult(order, g, network, tuple(warnings))
