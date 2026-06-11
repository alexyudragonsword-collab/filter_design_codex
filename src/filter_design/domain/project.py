"""Versioned project persistence."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .specifications import FilterSpecification


@dataclass(slots=True)
class FilterProject:
    specification: FilterSpecification
    name: str = "Untitled filter"
    version: int = 1

    def save(self, path: str | Path) -> None:
        payload = {"version": self.version, "name": self.name,
                   "specification": self.specification.to_dict()}
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "FilterProject":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("version") != 1:
            raise ValueError(f"Unsupported project version: {payload.get('version')}")
        return cls(FilterSpecification.from_dict(payload["specification"]),
                   payload.get("name", "Untitled filter"), payload["version"])
