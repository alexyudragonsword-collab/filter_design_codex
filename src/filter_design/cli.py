"""Command-line interface for repeatable filter design."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from filter_design.domain.project import FilterProject
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.exporters.csv_export import export_csv
from filter_design.exporters.report import export_html
from filter_design.exporters.spice import export_spice
from filter_design.exporters.touchstone import export_touchstone
from filter_design.formatting import engineering
from filter_design.workflow import design_filter, suggested_sweep


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="filter-design", description="Synthesize an ideal lumped LC filter")
    parser.add_argument("--project", type=Path, help="Load a .ofd.json project instead of command-line specs")
    parser.add_argument("--response", choices=[x.value for x in ResponseType], default="lowpass")
    parser.add_argument("--approximation", choices=[x.value for x in Approximation], default="butterworth")
    parser.add_argument("--passband", type=float, nargs="+", metavar="HZ", default=[1e6])
    parser.add_argument("--stopband", type=float, nargs="+", metavar="HZ", default=[2e6])
    parser.add_argument("--ripple", type=float, default=0.5, help="Passband ripple/attenuation in dB")
    parser.add_argument("--attenuation", type=float, default=40.0, help="Minimum stopband attenuation in dB")
    parser.add_argument("--impedance", type=float, default=50.0)
    parser.add_argument("--order", type=int)
    parser.add_argument("--points", type=int, default=701)
    parser.add_argument("--export-prefix", type=Path, help="Write CSV, S2P, CIR, HTML, and project files")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    return parser


def _spec(args: argparse.Namespace) -> FilterSpecification:
    if args.project:
        return FilterProject.load(args.project).specification
    return FilterSpecification(ResponseType(args.response), Approximation(args.approximation),
        tuple(args.passband), tuple(args.stopband), args.ripple, args.attenuation,
        args.impedance, args.impedance, args.order)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec = _spec(args)
        design = design_filter(spec, args.points)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        _parser().error(str(error))
    result = design.synthesis
    summary = {"order": result.order, "meets_passband": design.metrics.meets_passband,
               "meets_stopband": design.metrics.meets_stopband,
               "worst_passband_loss_db": design.metrics.worst_passband_loss_db,
               "minimum_stopband_attenuation_db": design.metrics.minimum_stopband_attenuation_db,
               "components": [{"reference": c.reference, "kind": c.kind.value,
                               "value": c.value, "unit": c.unit} for c in result.network.components],
               "warnings": list(result.warnings)}
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"{spec.approximation.value} {spec.response.value}, order {result.order}")
        for component in result.network.components:
            print(f"  {component.reference:<4} {engineering(component.value, component.unit)}")
        print(f"Passband worst loss: {design.metrics.worst_passband_loss_db:.3f} dB "
              f"({'PASS' if design.metrics.meets_passband else 'FAIL'})")
        print(f"Stopband minimum attenuation: {design.metrics.minimum_stopband_attenuation_db:.3f} dB "
              f"({'PASS' if design.metrics.meets_stopband else 'FAIL'})")
    if args.export_prefix:
        prefix = args.export_prefix
        prefix.parent.mkdir(parents=True, exist_ok=True)
        export_csv(prefix.with_suffix(".csv"), list(design.response))
        export_touchstone(prefix.with_suffix(".s2p"), list(design.response), spec.source_impedance_ohm)
        frequencies = suggested_sweep(spec, args.points)
        export_spice(prefix.with_suffix(".cir"), result.network, frequencies[0], frequencies[-1])
        export_html(prefix.with_suffix(".html"), spec, result, design.metrics)
        FilterProject(spec, prefix.stem).save(prefix.with_suffix(".ofd.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
