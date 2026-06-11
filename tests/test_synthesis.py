import math
import pytest

from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.synthesis.order import minimum_order
from filter_design.synthesis.prototypes import butterworth_g, chebyshev1_g
from filter_design.synthesis.service import synthesize_filter


def test_butterworth_third_order_coefficients():
    assert butterworth_g(3) == pytest.approx((1, 1, 2, 1, 1))


def test_chebyshev_coefficients_are_positive():
    values = chebyshev1_g(5, 0.5)
    assert len(values) == 7
    assert all(value > 0 and math.isfinite(value) for value in values)


def test_lowpass_order_and_component_count():
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.BUTTERWORTH,
                               (1e6,), (2e6,), 0.5, 40, 50, 50)
    assert minimum_order(spec) == 9
    result = synthesize_filter(spec)
    assert result.order == 9
    assert len(result.network.components) == 9


@pytest.mark.parametrize("response,passes,stops", [
    (ResponseType.LOWPASS, (1e6,), (2e6,)),
    (ResponseType.HIGHPASS, (2e6,), (1e6,)),
    (ResponseType.BANDPASS, (1e6, 2e6), (0.5e6, 3e6)),
    (ResponseType.BANDSTOP, (0.5e6, 3e6), (1e6, 2e6)),
])
def test_all_transformations_produce_finite_positive_components(response, passes, stops):
    spec = FilterSpecification(response, Approximation.CHEBYSHEV1, passes, stops,
                               0.5, 30, 50, 50, 4)
    result = synthesize_filter(spec)
    expected = 4 if response in (ResponseType.LOWPASS, ResponseType.HIGHPASS) else 8
    assert len(result.network.components) == expected
    assert all(math.isfinite(c.value) and c.value > 0 for c in result.network.components)
