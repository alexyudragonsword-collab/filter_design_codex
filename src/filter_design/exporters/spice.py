"""SPICE netlist export for synthesized ladders."""
from __future__ import annotations

from pathlib import Path

from filter_design.domain.network import BranchPosition, Connection, LadderNetwork


def _line(component, node_a: str, node_b: str) -> str:
    return f"{component.reference} {node_a} {node_b} {component.value:.12g}"


def export_spice(path: str | Path, network: LadderNetwork,
                 sweep_start_hz: float, sweep_stop_hz: float) -> None:
    lines = ["* Open Filter Designer generated netlist", "V1 source 0 AC 1",
             f"RS source n1 {network.source_impedance_ohm:.12g}"]
    current = "n1"
    next_node = 2
    for branch in network.branches:
        if branch.position == BranchPosition.SERIES:
            destination = f"n{next_node}"; next_node += 1
            if branch.connection == Connection.PARALLEL:
                lines.extend(_line(c, current, destination) for c in branch.components)
            else:
                node = current
                for index, component in enumerate(branch.components):
                    target = destination if index == len(branch.components) - 1 else f"n{next_node}"
                    if target != destination: next_node += 1
                    lines.append(_line(component, node, target)); node = target
            current = destination
        elif branch.connection == Connection.PARALLEL:
            lines.extend(_line(c, current, "0") for c in branch.components)
        else:
            node = current
            for index, component in enumerate(branch.components):
                target = "0" if index == len(branch.components) - 1 else f"n{next_node}"
                if target != "0": next_node += 1
                lines.append(_line(component, node, target)); node = target
    lines.extend([f"RL {current} 0 {network.load_impedance_ohm:.12g}",
                  f".ac dec 100 {sweep_start_hz:.12g} {sweep_stop_hz:.12g}",
                  f".print ac vdb({current})", ".end"])
    Path(path).write_text("\n".join(lines) + "\n", encoding="ascii")
