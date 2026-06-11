"""Ideal fully differential leapfrog active-RC realization."""
from __future__ import annotations

import math

from filter_design.domain.leapfrog import (
    LeapfrogComponent,
    LeapfrogComponentKind,
    LeapfrogCoupling,
    LeapfrogRealization,
    LeapfrogState,
)
from filter_design.domain.network import BranchPosition, ComponentKind, Connection, LadderNetwork
from filter_design.domain.specifications import FilterSpecification, ResponseType

_TARGET_COUPLING_RESISTANCE_OHM = 10_000.0
_MIN_INTEGRATING_CAPACITANCE_F = 10e-12
_MAX_INTEGRATING_CAPACITANCE_F = 1e-6


def _preferred_125(value: float) -> float:
    exponent = math.floor(math.log10(value))
    scale = 10.0**exponent
    normalized = value / scale
    preferred = min((1.0, 2.0, 5.0, 10.0), key=lambda candidate: abs(candidate - normalized))
    return preferred * scale


def _unsupported(specification: FilterSpecification, message: str) -> LeapfrogRealization:
    return LeapfrogRealization(
        supported=False,
        diagnostic=message,
        impedance_scale_ohm=specification.source_impedance_ohm,
    )


def _validate_lowpass_ladder(
    specification: FilterSpecification, network: LadderNetwork
) -> str | None:
    if specification.response != ResponseType.LOWPASS:
        return "Exact leapfrog realization currently supports low-pass LC ladders only."
    for index, branch in enumerate(network.branches):
        if len(branch.components) != 1 or branch.connection != Connection.SERIES:
            return "Leapfrog realization requires one non-resonant component per ladder branch."
        component = branch.components[0]
        expected_position = BranchPosition.SERIES if index % 2 == 0 else BranchPosition.SHUNT
        expected_kind = ComponentKind.INDUCTOR if index % 2 == 0 else ComponentKind.CAPACITOR
        if branch.position != expected_position or component.kind != expected_kind:
            return "Leapfrog realization requires an alternating series-L / shunt-C ladder."
    return None


def _state_coefficients(
    network: LadderNetwork,
) -> tuple[list[str], list[str], list[dict[str, float]], str, float]:
    """Build voltage-scaled low-pass ladder state equations."""
    z0 = network.source_impedance_ohm
    coefficients: list[dict[str, float]] = []
    references: list[str] = []
    variables: list[str] = []
    count = len(network.branches)

    for index, branch in enumerate(network.branches):
        component = branch.components[0]
        state = f"X{index + 1}"
        references.append(state)
        terms: dict[str, float] = {}
        if component.kind == ComponentKind.INDUCTOR:
            variables.append(f"{z0:g} ohm x i({component.reference})")
            factor = z0 / component.value
            if index == 0:
                terms["VIN"] = factor
                terms[state] = -network.source_impedance_ohm / component.value
            else:
                terms[f"X{index}"] = factor
            if index + 1 < count:
                terms[f"X{index + 2}"] = -factor
            else:
                terms[state] = terms.get(state, 0.0) - network.load_impedance_ohm / component.value
        else:
            variables.append(f"v({component.reference})")
            factor = 1.0 / (z0 * component.value)
            terms[f"X{index}"] = factor
            if index + 1 < count:
                terms[f"X{index + 2}"] = -factor
            else:
                terms[state] = terms.get(state, 0.0) - 1.0 / (
                    network.load_impedance_ohm * component.value
                )
        coefficients.append(terms)

    output_state = references[-1]
    last_component = network.branches[-1].components[0]
    output_gain = (
        network.load_impedance_ohm / z0
        if last_component.kind == ComponentKind.INDUCTOR
        else 1.0
    )
    return references, variables, coefficients, output_state, output_gain


def _equation(target: str, terms: dict[str, float]) -> str:
    pieces = []
    for source, coefficient in terms.items():
        sign = "+" if coefficient >= 0 else "-"
        pieces.append(f" {sign} {abs(coefficient):.6g}*{source}")
    expression = "".join(pieces).lstrip()
    if expression.startswith("+"):
        expression = expression[1:].lstrip()
    return f"d{target}/dt = {expression}"


def realize_fully_differential_leapfrog(
    specification: FilterSpecification, network: LadderNetwork
) -> LeapfrogRealization:
    """Create an exact ideal-op-amp leapfrog simulation of a low-pass ladder.

    Inductor-current states are multiplied by the source impedance so every
    state has voltage units. Each signed state coefficient is implemented by a
    differential resistor pair driving two inverting integrators. Positive
    terms are cross-coupled; negative terms are connected same-side.
    """
    diagnostic = _validate_lowpass_ladder(specification, network)
    if diagnostic:
        return _unsupported(specification, diagnostic)

    references, variables, matrix, output_state, output_gain = _state_coefficients(network)
    maximum_coefficient = max(abs(value) for row in matrix for value in row.values())
    raw_capacitance = 1.0 / (_TARGET_COUPLING_RESISTANCE_OHM * maximum_coefficient)
    bounded = min(
        max(raw_capacitance, _MIN_INTEGRATING_CAPACITANCE_F),
        _MAX_INTEGRATING_CAPACITANCE_F,
    )
    integrating_capacitance = _preferred_125(bounded)

    states: list[LeapfrogState] = []
    components: list[LeapfrogComponent] = []
    for state_index, (target, variable, terms) in enumerate(
        zip(references, variables, matrix, strict=True), start=1
    ):
        capacitor_references = (f"C_{target}_P", f"C_{target}_N")
        for side, reference in zip(("P", "N"), capacitor_references, strict=True):
            components.append(
                LeapfrogComponent(
                    reference=reference,
                    kind=LeapfrogComponentKind.CAPACITOR,
                    value=integrating_capacitance,
                    state=target,
                    side=side,
                    function="Leapfrog integrating capacitor",
                )
            )
        couplings: list[LeapfrogCoupling] = []
        for coupling_index, (source, coefficient) in enumerate(terms.items(), start=1):
            resistance = 1.0 / (abs(coefficient) * integrating_capacitance)
            references_pair = (
                f"R_{target}_{coupling_index}_P",
                f"R_{target}_{coupling_index}_N",
            )
            routing = "cross-coupled" if coefficient > 0 else "same-side"
            couplings.append(
                LeapfrogCoupling(
                    source=source,
                    target=target,
                    coefficient_per_second=coefficient,
                    routing=routing,
                    resistor_ohm=resistance,
                    resistor_references=references_pair,
                )
            )
            for side, reference in zip(("P", "N"), references_pair, strict=True):
                components.append(
                    LeapfrogComponent(
                        reference=reference,
                        kind=LeapfrogComponentKind.RESISTOR,
                        value=resistance,
                        state=target,
                        side=side,
                        function=f"{routing} input from {source}",
                    )
                )
        states.append(
            LeapfrogState(
                reference=target,
                source_component=network.branches[state_index - 1].components[0].reference,
                variable=variable,
                equation=_equation(target, terms),
                integrating_capacitance_f=integrating_capacitance,
                capacitor_references=capacitor_references,
                couplings=tuple(couplings),
            )
        )

    return LeapfrogRealization(
        supported=True,
        diagnostic=(
            "Ideal low-pass ladder simulation with two inverting op-amp integrators per state."
        ),
        impedance_scale_ohm=network.source_impedance_ohm,
        states=tuple(states),
        components=tuple(components),
        output_state=output_state,
        output_gain=output_gain,
    )
