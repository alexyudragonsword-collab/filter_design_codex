"""Circuit-domain objects shared by synthesis, analysis, and exporters."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ComponentKind(StrEnum):
    INDUCTOR = "L"
    CAPACITOR = "C"


class BranchPosition(StrEnum):
    SERIES = "series"
    SHUNT = "shunt"


class Connection(StrEnum):
    SERIES = "series"
    PARALLEL = "parallel"


@dataclass(frozen=True, slots=True)
class Component:
    kind: ComponentKind
    value: float
    reference: str

    @property
    def unit(self) -> str:
        return "H" if self.kind == ComponentKind.INDUCTOR else "F"

    def impedance(self, angular_frequency: float) -> complex:
        if self.kind == ComponentKind.INDUCTOR:
            return 1j * angular_frequency * self.value
        return 1 / (1j * angular_frequency * self.value)


@dataclass(frozen=True, slots=True)
class Branch:
    position: BranchPosition
    connection: Connection
    components: tuple[Component, ...]

    def impedance(self, angular_frequency: float) -> complex:
        impedances = [item.impedance(angular_frequency) for item in self.components]
        if self.connection == Connection.SERIES:
            return sum(impedances, 0j)
        admittance = sum((1 / item for item in impedances), 0j)
        return 1 / admittance


@dataclass(frozen=True, slots=True)
class LadderNetwork:
    branches: tuple[Branch, ...]
    source_impedance_ohm: float
    load_impedance_ohm: float

    @property
    def components(self) -> tuple[Component, ...]:
        return tuple(component for branch in self.branches for component in branch.components)


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    order: int
    prototype_g: tuple[float, ...]
    network: LadderNetwork
    warnings: tuple[str, ...] = field(default_factory=tuple)
