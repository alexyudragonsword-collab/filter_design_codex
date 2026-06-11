"""Engineering-number formatting shared by UI and reports."""
from __future__ import annotations

_PREFIXES = ((1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""),
             (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p"))


def engineering(value: float, unit: str = "", digits: int = 4) -> str:
    if value == 0:
        return f"0 {unit}".strip()
    magnitude = abs(value)
    for scale, prefix in _PREFIXES:
        if magnitude >= scale * 0.999:
            return f"{value / scale:.{digits}g} {prefix}{unit}".strip()
    return f"{value:.{digits}g} {unit}".strip()
