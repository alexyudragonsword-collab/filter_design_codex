"""Classical normalized all-pole low-pass prototypes."""
from __future__ import annotations

import math

from filter_design.domain.specifications import Approximation


def butterworth_g(order: int) -> tuple[float, ...]:
    """Return g0..g(n+1) for a doubly terminated Butterworth ladder."""
    return (1.0, *(2 * math.sin((2 * k - 1) * math.pi / (2 * order))
                         for k in range(1, order + 1)), 1.0)


def chebyshev1_g(order: int, ripple_db: float) -> tuple[float, ...]:
    """Return equal-termination Chebyshev-I prototype coefficients."""
    beta = math.asinh(1 / math.sqrt(10 ** (ripple_db / 10) - 1)) / order
    gamma = math.sinh(beta)
    a = [0.0] + [math.sin((2 * k - 1) * math.pi / (2 * order))
                       for k in range(1, order + 1)]
    b = [gamma * gamma + math.sin(k * math.pi / order) ** 2
         for k in range(order + 1)]
    values = [1.0, 2 * a[1] / gamma]
    for k in range(2, order + 1):
        values.append(4 * a[k - 1] * a[k] / (b[k - 1] * values[k - 1]))
    load = 1.0 if order % 2 else 1 / math.tanh(beta / 2) ** 2
    values.append(load)
    return tuple(values)


def prototype_g(approximation: Approximation, order: int,
                ripple_db: float) -> tuple[float, ...]:
    if approximation == Approximation.BUTTERWORTH:
        return butterworth_g(order)
    return chebyshev1_g(order, ripple_db)
