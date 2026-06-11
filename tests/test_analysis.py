import pytest

from filter_design.analysis.response import logarithmic_sweep, s_parameters
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.synthesis.service import synthesize_filter
from filter_design.workflow import design_filter


def test_lossless_network_conserves_power():
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.BUTTERWORTH,
                               (1e6,), (2e6,), 0.5, 40, 50, 50)
    network = synthesize_filter(spec).network
    for frequency in (1e5, 1e6, 1e7):
        s11, s21, s12, _ = s_parameters(network, frequency)
        assert abs(s11) ** 2 + abs(s21) ** 2 == pytest.approx(1, abs=1e-10)
        assert s12 == pytest.approx(s21)


def test_designed_lowpass_meets_sampled_specification():
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.BUTTERWORTH,
                               (1e6,), (2e6,), 0.5, 40, 50, 50)
    design = design_filter(spec, 1201)
    assert design.metrics.meets_passband
    assert design.metrics.meets_stopband


def test_log_sweep_includes_endpoints():
    sweep = logarithmic_sweep(1e3, 1e6, 4)
    assert sweep == pytest.approx([1e3, 1e4, 1e5, 1e6])

@pytest.mark.parametrize("response,passes,stops", [
    (ResponseType.HIGHPASS, (2e6,), (1e6,)),
    (ResponseType.BANDPASS, (1e6, 2e6), (0.5e6, 3e6)),
    (ResponseType.BANDSTOP, (0.5e6, 3e6), (1e6, 2e6)),
])
def test_automatic_butterworth_designs_meet_specs(response, passes, stops):
    spec = FilterSpecification(response, Approximation.BUTTERWORTH, passes, stops,
                               0.5, 30, 50, 50)
    design = design_filter(spec, 1601)
    assert design.metrics.meets_passband
    assert design.metrics.meets_stopband


def test_equal_termination_chebyshev_promotes_even_order():
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.CHEBYSHEV1,
                               (1e6,), (2e6,), 0.5, 30, 50, 50)
    design = design_filter(spec, 1201)
    assert design.synthesis.order % 2 == 1
    assert design.metrics.meets_passband
    assert design.metrics.meets_stopband
    assert "next odd value" in design.synthesis.warnings[0]
