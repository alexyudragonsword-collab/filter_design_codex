"""CSV response export."""
from __future__ import annotations

import csv
from pathlib import Path

from filter_design.analysis.response import ResponsePoint


def export_csv(path: str | Path, response: list[ResponsePoint]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frequency_hz", "s11_real", "s11_imag", "s21_real", "s21_imag",
                         "insertion_loss_db", "return_loss_db", "phase_deg", "group_delay_s"])
        for point in response:
            writer.writerow([point.frequency_hz, point.s11.real, point.s11.imag,
                             point.s21.real, point.s21.imag, point.insertion_loss_db,
                             point.return_loss_db, point.phase_deg, point.group_delay_s])
