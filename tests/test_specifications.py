import json
import pytest

from filter_design.domain.project import FilterProject
from filter_design.domain.specifications import Approximation, FilterSpecification, ResponseType


def test_valid_lowpass_and_project_roundtrip(tmp_path):
    spec = FilterSpecification(ResponseType.LOWPASS, Approximation.BUTTERWORTH,
                               (1e6,), (2e6,), 0.5, 40, 50, 50)
    path = tmp_path / "filter.ofd.json"
    FilterProject(spec, "Example").save(path)
    loaded = FilterProject.load(path)
    assert loaded.name == "Example"
    assert loaded.specification == spec
    assert json.loads(path.read_text())["version"] == 1


@pytest.mark.parametrize("response,passes,stops", [
    (ResponseType.LOWPASS, (2e6,), (1e6,)),
    (ResponseType.HIGHPASS, (1e6,), (2e6,)),
    (ResponseType.BANDPASS, (1e6, 2e6), (1.2e6, 3e6)),
    (ResponseType.BANDSTOP, (1e6, 2e6), (0.5e6, 1.5e6)),
])
def test_invalid_edge_order(response, passes, stops):
    with pytest.raises(ValueError):
        FilterSpecification(response, Approximation.BUTTERWORTH, passes, stops)
