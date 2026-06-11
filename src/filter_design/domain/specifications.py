"""Validated filter specifications and enums."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class ResponseType(StrEnum):
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    BANDSTOP = "bandstop"


class Approximation(StrEnum):
    BUTTERWORTH = "butterworth"
    CHEBYSHEV1 = "chebyshev1"


@dataclass(frozen=True, slots=True)
class FilterSpecification:
    """Electrical requirements in SI units.

    Single-ended filters use ``passband_hz[0]`` and ``stopband_hz[0]``.
    Double-ended filters use both tuple entries. For a band-pass design the
    stop edges surround the pass band; for band-stop the pass edges surround
    the stop band.
    """

    response: ResponseType
    approximation: Approximation
    passband_hz: tuple[float, ...]
    stopband_hz: tuple[float, ...]
    passband_ripple_db: float = 0.1
    stopband_attenuation_db: float = 40.0
    source_impedance_ohm: float = 50.0
    load_impedance_ohm: float = 50.0
    order: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "response", ResponseType(self.response))
        object.__setattr__(self, "approximation", Approximation(self.approximation))
        object.__setattr__(self, "passband_hz", tuple(float(x) for x in self.passband_hz))
        object.__setattr__(self, "stopband_hz", tuple(float(x) for x in self.stopband_hz))
        self.validate()

    def validate(self) -> None:
        if any(not x > 0 for x in (*self.passband_hz, *self.stopband_hz)):
            raise ValueError("All edge frequencies must be greater than zero")
        if self.source_impedance_ohm <= 0 or self.load_impedance_ohm <= 0:
            raise ValueError("Source and load impedances must be greater than zero")
        if self.stopband_attenuation_db <= 0:
            raise ValueError("Stopband attenuation must be greater than zero")
        if self.passband_ripple_db <= 0:
            raise ValueError("Passband ripple must be greater than zero")
        if self.order is not None and not 1 <= self.order <= 30:
            raise ValueError("Order must be between 1 and 30")
        if self.response in (ResponseType.LOWPASS, ResponseType.HIGHPASS):
            if len(self.passband_hz) != 1 or len(self.stopband_hz) != 1:
                raise ValueError("Low/high-pass designs require one pass and stop edge")
            fp, fs = self.passband_hz[0], self.stopband_hz[0]
            if self.response == ResponseType.LOWPASS and fp >= fs:
                raise ValueError("Low-pass requires passband edge < stopband edge")
            if self.response == ResponseType.HIGHPASS and fp <= fs:
                raise ValueError("High-pass requires stopband edge < passband edge")
        else:
            if len(self.passband_hz) != 2 or len(self.stopband_hz) != 2:
                raise ValueError("Band designs require two pass and two stop edges")
            p1, p2 = self.passband_hz
            s1, s2 = self.stopband_hz
            if self.response == ResponseType.BANDPASS and not s1 < p1 < p2 < s2:
                raise ValueError("Band-pass edges must satisfy stop1 < pass1 < pass2 < stop2")
            if self.response == ResponseType.BANDSTOP and not p1 < s1 < s2 < p2:
                raise ValueError("Band-stop edges must satisfy pass1 < stop1 < stop2 < pass2")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["response"] = self.response.value
        data["approximation"] = self.approximation.value
        data["passband_hz"] = list(self.passband_hz)
        data["stopband_hz"] = list(self.stopband_hz)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "FilterSpecification":
        return cls(**data)
