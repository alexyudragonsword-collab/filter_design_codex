"""Convert an ideal LC ladder to a symmetric fully differential active-RC network."""
from __future__ import annotations

import math

from filter_design.domain.active_rc import (
    ActiveComponentKind,
    ActiveRCBranch,
    ActiveRCComponent,
    ActiveRCStage,
    FullyDifferentialRealization,
)
from filter_design.domain.network import ComponentKind, LadderNetwork

_GIC_TARGET_RESISTANCE_OHM = 1_000.0
_GIC_MIN_CAPACITANCE_F = 10e-12
_GIC_MAX_CAPACITANCE_F = 100e-9


def _preferred_125(value: float) -> float:
    """Round a positive value to the nearest 1-2-5 engineering value."""
    exponent = math.floor(math.log10(value))
    scale = 10.0**exponent
    normalized = value / scale
    preferred = min((1.0, 2.0, 5.0, 10.0), key=lambda candidate: abs(candidate - normalized))
    return preferred * scale


def _gic_values(inductance_h: float) -> tuple[float, float]:
    """Choose equal Antoniou-GIC resistors and a practical capacitor.

    With R1 = R2 = R3 = R5 = R, the ideal GIC input impedance is
    ``s * C * R**2`` and therefore simulates ``L = C * R**2``.
    """
    raw_capacitance = inductance_h / (_GIC_TARGET_RESISTANCE_OHM**2)
    bounded = min(max(raw_capacitance, _GIC_MIN_CAPACITANCE_F), _GIC_MAX_CAPACITANCE_F)
    capacitance = _preferred_125(bounded)
    resistance = math.sqrt(inductance_h / capacitance)
    return resistance, capacitance


def _capacitor_stage(component, branch) -> ActiveRCStage:
    # Two impedances of Z/2, one in each signal leg, preserve the differential Z.
    leg_capacitance = 2.0 * component.value
    physical = tuple(
        ActiveRCComponent(
            reference=f"{component.reference}_{side}",
            kind=ActiveComponentKind.CAPACITOR,
            value=leg_capacitance,
            stage=component.reference,
            side=side,
            function=f"Differential half of {component.reference}",
        )
        for side in ("P", "N")
    )
    return ActiveRCStage(
        source_reference=component.reference,
        position=branch.position,
        connection=branch.connection,
        cell_type="Symmetric capacitor pair",
        positive_label=physical[0].reference,
        negative_label=physical[1].reference,
        components=physical,
        op_amp_count=0,
        design_note=f"Each leg uses 2 x {component.reference} capacitance to preserve differential impedance.",
    )


def _inductor_stage(component, branch) -> ActiveRCStage:
    # Each signal leg must realize half of the original inductance.
    leg_inductance = component.value / 2.0
    resistance, capacitance = _gic_values(leg_inductance)
    physical: list[ActiveRCComponent] = []
    labels: list[str] = []
    for side in ("P", "N"):
        cell = f"{component.reference}_{side}"
        labels.append(f"GIC {cell}")
        for resistor_index in (1, 2, 3, 5):
            physical.append(
                ActiveRCComponent(
                    reference=f"R_{cell}_{resistor_index}",
                    kind=ActiveComponentKind.RESISTOR,
                    value=resistance,
                    stage=component.reference,
                    side=side,
                    function=f"Antoniou GIC R{resistor_index}",
                )
            )
        physical.append(
            ActiveRCComponent(
                reference=f"C_{cell}_4",
                kind=ActiveComponentKind.CAPACITOR,
                value=capacitance,
                stage=component.reference,
                side=side,
                function="Antoniou GIC energy-storage capacitor",
            )
        )
    return ActiveRCStage(
        source_reference=component.reference,
        position=branch.position,
        connection=branch.connection,
        cell_type="Dual Antoniou GIC simulated inductor",
        positive_label=labels[0],
        negative_label=labels[1],
        components=tuple(physical),
        op_amp_count=4,
        design_note=(
            f"Each leg simulates L={leg_inductance:.12g} H with two ideal op-amps; "
            "equal GIC resistors satisfy L=C*R^2."
        ),
    )


def realize_fully_differential(network: LadderNetwork) -> FullyDifferentialRealization:
    """Return an ideal symmetric active-RC implementation of ``network``.

    Capacitors are split into equal positive and negative leg components. Every
    inductor is replaced by two mirrored Antoniou GIC cells, each simulating
    half of the original inductance. The transformation preserves differential
    impedance under ideal op-amp and virtual-common-mode assumptions.
    """
    active_branches: list[ActiveRCBranch] = []
    for branch_index, branch in enumerate(network.branches, start=1):
        stages: list[ActiveRCStage] = []
        for component in branch.components:
            if component.kind == ComponentKind.CAPACITOR:
                stages.append(_capacitor_stage(component, branch))
            else:
                stages.append(_inductor_stage(component, branch))
        active_branches.append(
            ActiveRCBranch(
                reference=f"B{branch_index}",
                position=branch.position,
                connection=branch.connection,
                stages=tuple(stages),
            )
        )
    return FullyDifferentialRealization(tuple(active_branches))
