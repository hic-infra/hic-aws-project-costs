from difflib import unified_diff
from pathlib import Path

import yaml

from aws_project_costs.project_costs import analyse_costs_csv

# from aws_project_costs.schema import validate

EXAMPLE_DIR = Path(__file__).parent / ".." / "example"


def test_analyse_costs_csv(tmp_path):
    config_yaml = EXAMPLE_DIR / "projects.yaml"
    input_csv = EXAMPLE_DIR / "2024-01-01_2024-02-01.csv"
    output_csv = tmp_path / "output.csv"
    reference_csv = EXAMPLE_DIR / "output.csv"

    with (config_yaml).open() as f:
        cfg = yaml.safe_load(f)
    analyse_costs_csv(cfg, input_csv, output_csv)

    reference = reference_csv.read_text().splitlines()
    output = output_csv.read_text().splitlines()
    diff = list(unified_diff(reference, output))
    assert not diff, "\n".join(diff)
