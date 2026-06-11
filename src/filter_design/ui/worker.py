"""Background worker used to keep Qt responsive during design analysis."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from filter_design.domain.specifications import FilterSpecification
from filter_design.workflow import design_filter


class DesignWorker(QObject):
    """Runs the UI-independent workflow in a QThread."""

    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, specification: FilterSpecification, points: int = 1001) -> None:
        super().__init__()
        self.specification = specification
        self.points = points

    @Slot()
    def run(self) -> None:
        try:
            design = design_filter(self.specification, self.points)
        except (ArithmeticError, ValueError) as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit(design)
        finally:
            self.finished.emit()
