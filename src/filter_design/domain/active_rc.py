"""Fully differential op-amp-RC realization data models."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .network import BranchPosition, Connection


class ActiveComponentKind(StrEnum):
    RESISTOR = "R"
    CAPACITOR = "C"


@dataclass(frozen=True, slots=True)
class ActiveRCComponent:
    """A physical resistor or capacitor used by an active-RC cell."""

    reference: str
    kind: ActiveComponentKind
    value: float
    stage: str
    side: str
    function: str

    @property
    def unit(self) -> str:
        return "ohm" if self.kind == ActiveComponentKind.RESISTOR else "F"


@dataclass(frozen=True, slots=True)
class ActiveRCStage:
    """A differential replacement for one component in the LC ladder."""

    source_reference: str
    position: BranchPosition
    connection: Connection
    cell_type: str
    positive_label: str
    negative_label: str
    components: tuple[ActiveRCComponent, ...]
    op_amp_count: int
    design_note: str


@dataclass(frozen=True, slots=True)
class ActiveRCBranch:
    """One differential ladder branch containing one or more active-RC stages."""

    reference: str
    position: BranchPosition
    connection: Connection
    stages: tuple[ActiveRCStage, ...]


@dataclass(frozen=True, slots=True)
class FullyDifferentialRealization:
    """A symmetric two-leg active-RC implementation of a ladder network."""

    branches: tuple[ActiveRCBranch, ...]
    common_mode_label: str = "VCM"

    @property
    def stages(self) -> tuple[ActiveRCStage, ...]:
        return tuple(stage for branch in self.branches for stage in branch.stages)

    @property
    def components(self) -> tuple[ActiveRCComponent, ...]:
        return tuple(component for stage in self.stages for component in stage.components)

    @property
    def resistor_count(self) -> int:
        return sum(component.kind == ActiveComponentKind.RESISTOR for component in self.components)

    @property
    def capacitor_count(self) -> int:
        return sum(component.kind == ActiveComponentKind.CAPACITOR for component in self.components)

    @property
    def op_amp_count(self) -> int:
        return sum(stage.op_amp_count for stage in self.stages)
