import csv

from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType
from filter_design.exporters.csv_export import export_csv
from filter_design.exporters.report import export_html
from filter_design.exporters.spice import export_spice
from filter_design.exporters.touchstone import export_touchstone
from filter_design.workflow import design_filter, suggested_sweep


def test_export_formats(tmp_path):
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.BUTTERWORTH,
                               (1e6,), (2e6,), 0.5, 30, 50, 50, 5)
    design = design_filter(spec, 101)
    csv_path, s2p, cir, html = (tmp_path / name for name in ("r.csv", "r.s2p", "r.cir", "r.html"))
    export_csv(csv_path, list(design.response))
    export_touchstone(s2p, list(design.response), 50)
    sweep = suggested_sweep(spec)
    export_spice(cir, design.synthesis.network, sweep[0], sweep[-1])
    export_html(html, spec, design.synthesis, design.metrics)
    with csv_path.open() as stream:
        assert len(list(csv.reader(stream))) == 102
    data_lines = [line for line in s2p.read_text().splitlines() if not line.startswith(("!", "#"))]
    assert len(data_lines[0].split()) == 9
    assert ".ac dec" in cir.read_text()
    assert "Open Filter Designer report" in html.read_text()
