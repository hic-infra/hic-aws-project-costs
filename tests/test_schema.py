from pathlib import Path

import pytest
import yaml

from aws_project_costs.schema import validate

EXAMPLE_DIR = Path(__file__).parent / ".." / "example"


def test_schema_validate_example():
    config_yaml = EXAMPLE_DIR / "projects.yaml"
    with (config_yaml).open() as f:
        cfg = yaml.safe_load(f)
    errors = validate(cfg, raise_on_error=False)
    assert len(errors) == 0


@pytest.mark.parametrize("raise_on_error", [True, False])
def test_schema_validate_errors(raise_on_error):
    config_yaml = """
proj-tag-names:
  project-001: Project A

accounts:
  - name: aws-auth
    billing-type: shared
    project-tagname: Proj
    project-groups:
      - tre
      - non-existent

  - name: aws-AUTH
    billing-type: project-specific
    project: x

  - name: invalid-costshare
    billing-type: shared
    project-groups:
      - invalid

project-groups:
  tre:
    - name: Project A
      costshare: 1
    - name: Project B
      costshare: 0
  web:
    - name: Project A
      costshare: 2
    - name: Project C
      costshare: 1
  invalid:
    - name: Project D
      costshare: 0
"""
    cfg = yaml.safe_load(config_yaml)

    if raise_on_error:
        with pytest.raises(ValueError) as excinfo:
            validate(cfg, raise_on_error=raise_on_error)
        errors = excinfo.value.args[0]
    else:
        errors = validate(cfg, raise_on_error=raise_on_error)

    assert len(errors) == 3
    expected_errors = [
        "project-group non-existent in account aws-auth does not exist!",
        "Multiple entries for account name=aws-auth",
        "All projects in project-group invalid have costshare=0",
    ]
    assert errors == expected_errors
