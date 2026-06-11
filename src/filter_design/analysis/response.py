"""ABCD cascade and two-port response calculations."""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math

from filter_design.domain.network import BranchPosition, LadderNetwork

Matrix = tuple[complex, complex, complex, complex]


@dataclass(frozen=True, slots=True)
class ResponsePoint:
    frequency_hz: float
    s11: complex
    s21: complex
    s12: complex
    s22: complex
    insertion_loss_db: float
    return_loss_db: float
    phase_deg: float
    group_delay_s: float = 0.0


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    a, b, c, d = left
    e, f, g, h = right
    return (a * e + b * g, a * f + b * h,
            c * e + d * g, c * f + d * h)


def abcd(network: LadderNetwork, frequency_hz: float) -> Matrix:
    if frequency_hz <= 0:
        raise ValueError("Analysis frequency must be greater than zero")
    matrix: Matrix = (1 + 0j, 0j, 0j, 1 + 0j)
    omega = 2 * math.pi * frequency_hz
    for branch in network.branches:
        impedance = branch.impedance(omega)
        if branch.position == BranchPosition.SERIES:
            branch_matrix = (1 + 0j, impedance, 0j, 1 + 0j)
        else:
            if abs(impedance) < 1e-300:
                admittance = complex(1e300, 0)
            elif math.isinf(abs(impedance)):
                admittance = 0j
            else:
                admittance = 1 / impedance
            branch_matrix = (1 + 0j, 0j, admittance, 1 + 0j)
        matrix = _multiply(matrix, branch_matrix)
    return matrix


def s_parameters(network: LadderNetwork, frequency_hz: float) -> tuple[complex, complex, complex, complex]:
    a, b, c, d = abcd(network, frequency_hz)
    z1, z2 = network.source_impedance_ohm, network.load_impedance_ohm
    denominator = a * z2 + b + c * z1 * z2 + d * z1
    if abs(denominator) < 1e-300:
        return complex(1, 0), 0j, 0j, complex(1, 0)
    s11 = (a * z2 + b - c * z1 * z2 - d * z1) / denominator
    s21 = 2 * math.sqrt(z1 * z2) / denominator
    # Every supported ladder is reciprocal; assigning directly also avoids
    # catastrophic cancellation in the ABCD determinant deep in a stopband.
    s12 = s21
    s22 = (-a * z2 + b - c * z1 * z2 + d * z1) / denominator
    return s11, s21, s12, s22


def _db(value: complex) -> float:
    return 20 * math.log10(max(abs(value), 1e-300))


def analyze(network: LadderNetwork, frequencies_hz: list[float]) -> list[ResponsePoint]:
    if len(frequencies_hz) < 2:
        raise ValueError("At least two frequency points are required")
    raw: list[tuple[float, complex, complex, complex, complex, float]] = []
    previous_phase: float | None = None
    unwrapped = 0.0
    for frequency in frequencies_hz:
        s11, s21, s12, s22 = s_parameters(network, frequency)
        phase = cmath.phase(s21)
        if previous_phase is None:
            unwrapped = phase
        else:
            delta = phase - previous_phase
            while delta > math.pi:
                delta -= 2 * math.pi
            while delta < -math.pi:
                delta += 2 * math.pi
            unwrapped += delta
        raw.append((frequency, s11, s21, s12, s22, unwrapped))
        previous_phase = phase
    delays = [0.0] * len(raw)
    for i in range(len(raw)):
        lo, hi = max(0, i - 1), min(len(raw) - 1, i + 1)
        if hi != lo:
            delays[i] = -(raw[hi][5] - raw[lo][5]) / (2 * math.pi * (raw[hi][0] - raw[lo][0]))
    return [ResponsePoint(f, s11, s21, s12, s22, -_db(s21), -_db(s11),
                          math.degrees(phase), delays[i])
            for i, (f, s11, s21, s12, s22, phase) in enumerate(raw)]


def logarithmic_sweep(start_hz: float, stop_hz: float, points: int = 501) -> list[float]:
    if not 0 < start_hz < stop_hz:
        raise ValueError("Sweep requires 0 < start < stop")
    if points < 2:
        raise ValueError("Sweep requires at least two points")
    start, step = math.log10(start_hz), (math.log10(stop_hz) - math.log10(start_hz)) / (points - 1)
    return [10 ** (start + index * step) for index in range(points)]
