import pytest

from filter_design.domain.leapfrog import LeapfrogComponentKind
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.realization.leapfrog import realize_fully_differential_leapfrog
from filter_design.synthesis.service import synthesize_filter


def _spec(response=ResponseType.LOWPASS):
    if response == ResponseType.LOWPASS:
        passband, stopband = (1e6,), (2e6,)
    else:
        passband, stopband = (2e6,), (1e6,)
    return FilterSpecification(
        response, Approximation.BUTTERWORTH, passband, stopband, 0.5, 40, 50, 50
    )


def test_default_lowpass_leapfrog_has_one_integrator_per_ladder_element():
    specification = _spec()
    network = synthesize_filter(specification).network
    realization = realize_fully_differential_leapfrog(specification, network)
    assert realization.supported
    assert len(realization.states) == len(network.components) == 9
    assert realization.op_amp_count == 18
    assert realization.capacitor_count == 18
    assert realization.output_state == "X9"
    assert realization.output_gain == pytest.approx(1.0)


def test_rc_values_reproduce_every_state_coefficient():
    specification = _spec()
    network = synthesize_filter(specification).network
    realization = realize_fully_differential_leapfrog(specification, network)
    for state in realization.states:
        for coupling in state.couplings:
            reconstructed = 1.0 / (
                coupling.resistor_ohm * state.integrating_capacitance_f
            )
            assert reconstructed == pytest.approx(abs(coupling.coefficient_per_second))
            assert coupling.routing == (
                "cross-coupled" if coupling.coefficient_per_second > 0 else "same-side"
            )
            physical = [
                component
                for component in realization.components
                if component.reference in coupling.resistor_references
            ]
            assert len(physical) == 2
            assert all(component.kind == LeapfrogComponentKind.RESISTOR for component in physical)


def test_first_and_last_state_include_source_and_load_damping():
    specification = _spec()
    network = synthesize_filter(specification).network
    realization = realize_fully_differential_leapfrog(specification, network)
    first = realization.states[0]
    assert {coupling.source for coupling in first.couplings} >= {"VIN", "X1", "X2"}
    assert next(c for c in first.couplings if c.source == "VIN").coefficient_per_second > 0
    assert next(c for c in first.couplings if c.source == "X1").coefficient_per_second < 0
    last = realization.states[-1]
    assert next(c for c in last.couplings if c.source == "X9").coefficient_per_second < 0


def test_non_lowpass_response_reports_unsupported_instead_of_fabricating_values():
    specification = _spec(ResponseType.HIGHPASS)
    network = synthesize_filter(specification).network
    realization = realize_fully_differential_leapfrog(specification, network)
    assert not realization.supported
    assert not realization.states
    assert not realization.components
    assert "low-pass" in realization.diagnostic


def _solve_complex(matrix, vector):
    size = len(vector)
    augmented = [list(row) + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        assert abs(divisor) > 1e-30
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [augmented[index][-1] for index in range(size)]


def test_leapfrog_state_equations_match_the_lc_voltage_transfer():
    from filter_design.analysis.response import s_parameters

    specification = _spec()
    network = synthesize_filter(specification).network
    realization = realize_fully_differential_leapfrog(specification, network)
    state_index = {state.reference: index for index, state in enumerate(realization.states)}
    for frequency in (0.2e6, 1e6, 2e6):
        omega = 2 * 3.141592653589793 * frequency
        matrix = [[0j for _ in realization.states] for _ in realization.states]
        drive = [0j for _ in realization.states]
        for row, state in enumerate(realization.states):
            matrix[row][row] = 1j * omega
            for coupling in state.couplings:
                if coupling.source == "VIN":
                    drive[row] += coupling.coefficient_per_second
                else:
                    matrix[row][state_index[coupling.source]] -= coupling.coefficient_per_second
        solution = _solve_complex(matrix, drive)
        voltage_transfer = realization.output_gain * solution[state_index[realization.output_state]]
        _, s21, _, _ = s_parameters(network, frequency)
        assert 2 * voltage_transfer == pytest.approx(s21, abs=1e-9)
