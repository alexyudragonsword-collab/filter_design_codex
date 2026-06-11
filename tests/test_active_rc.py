import pytest

from filter_design.domain.active_rc import ActiveComponentKind
from filter_design.domain.network import ComponentKind
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.realization.fully_differential import realize_fully_differential
from filter_design.synthesis.service import synthesize_filter


def _default_network():
    specification = FilterSpecification(
        ResponseType.LOWPASS,
        Approximation.BUTTERWORTH,
        (1e6,),
        (2e6,),
        0.5,
        40,
        50,
        50,
    )
    return synthesize_filter(specification).network


def test_fully_differential_realization_has_one_stage_per_lc_component():
    network = _default_network()
    realization = realize_fully_differential(network)
    assert len(realization.stages) == len(network.components)
    assert realization.op_amp_count == 20
    assert realization.resistor_count == 40
    assert realization.capacitor_count == 18


def test_capacitor_pairs_preserve_differential_impedance():
    network = _default_network()
    realization = realize_fully_differential(network)
    source_components = {component.reference: component for component in network.components}
    for stage in realization.stages:
        source = source_components[stage.source_reference]
        if source.kind != ComponentKind.CAPACITOR:
            continue
        assert stage.op_amp_count == 0
        assert len(stage.components) == 2
        assert all(component.kind == ActiveComponentKind.CAPACITOR for component in stage.components)
        assert all(component.value == pytest.approx(2 * source.value) for component in stage.components)


def test_equal_resistor_gic_cells_simulate_half_the_source_inductance():
    network = _default_network()
    realization = realize_fully_differential(network)
    source_components = {component.reference: component for component in network.components}
    for stage in realization.stages:
        source = source_components[stage.source_reference]
        if source.kind != ComponentKind.INDUCTOR:
            continue
        assert stage.op_amp_count == 4
        for side in ("P", "N"):
            side_parts = [component for component in stage.components if component.side == side]
            resistors = [part for part in side_parts if part.kind == ActiveComponentKind.RESISTOR]
            capacitors = [part for part in side_parts if part.kind == ActiveComponentKind.CAPACITOR]
            assert len(resistors) == 4
            assert len(capacitors) == 1
            assert all(resistor.value == pytest.approx(resistors[0].value) for resistor in resistors)
            simulated_inductance = capacitors[0].value * resistors[0].value**2
            assert simulated_inductance == pytest.approx(source.value / 2)


def test_bandpass_realization_preserves_branch_grouping_and_connections():
    specification = FilterSpecification(
        ResponseType.BANDPASS,
        Approximation.BUTTERWORTH,
        (1e6, 2e6),
        (0.5e6, 3e6),
        0.5,
        30,
        50,
        50,
        4,
    )
    network = synthesize_filter(specification).network
    realization = realize_fully_differential(network)
    assert len(realization.branches) == len(network.branches)
    for active_branch, source_branch in zip(
        realization.branches, network.branches, strict=True
    ):
        assert active_branch.position == source_branch.position
        assert active_branch.connection == source_branch.connection
        assert [stage.source_reference for stage in active_branch.stages] == [
            component.reference for component in source_branch.components
        ]
