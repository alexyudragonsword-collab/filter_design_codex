"""Domain objects for an ideal fully differential leapfrog active-RC filter."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LeapfrogComponentKind(StrEnum):
    RESISTOR = "R"
    CAPACITOR = "C"


@dataclass(frozen=True, slots=True)
class LeapfrogComponent:
    """A physical component in one side of a differential integrator."""

    reference: str
    kind: LeapfrogComponentKind
    value: float
    state: str
    side: str
    function: str

    @property
    def unit(self) -> str:
        return "ohm" if self.kind == LeapfrogComponentKind.RESISTOR else "F"


@dataclass(frozen=True, slots=True)
class LeapfrogCoupling:
    """One signed term in a leapfrog state equation."""

    source: str
    target: str
    coefficient_per_second: float
    routing: str
    resistor_ohm: float
    resistor_references: tuple[str, str]


@dataclass(frozen=True, slots=True)
class LeapfrogState:
    """A voltage-mode differential integrator state."""

    reference: str
    source_component: str
    variable: str
    equation: str
    integrating_capacitance_f: float
    capacitor_references: tuple[str, str]
    couplings: tuple[LeapfrogCoupling, ...]


@dataclass(frozen=True, slots=True)
class LeapfrogRealization:
    """An ideal differential leapfrog simulation of an LC ladder."""

    supported: bool
    diagnostic: str
    impedance_scale_ohm: float
    states: tuple[LeapfrogState, ...] = ()
    components: tuple[LeapfrogComponent, ...] = ()
    output_state: str | None = None
    output_gain: float = 1.0
    common_mode_label: str = "VCM"

    @property
    def op_amp_count(self) -> int:
        return 2 * len(self.states)

    @property
    def resistor_count(self) -> int:
        return sum(component.kind == LeapfrogComponentKind.RESISTOR for component in self.components)

    @property
    def capacitor_count(self) -> int:
        return sum(component.kind == LeapfrogComponentKind.CAPACITOR for component in self.components)
