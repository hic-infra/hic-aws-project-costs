import json
import sys
from pathlib import Path

import jsonschema
import yaml


def validate(projects, raise_on_error=False):
    with (Path(__file__).resolve().parent / "project-cost-schema.json").open() as f:
        schema = json.load(f)

    jsonschema.validate(projects, schema)

    errors = []

    # Check accounts[].project-groups are valid
    # Check accounts[].name are unique
    # Check at least one project in project-groups has a non-zero costshare
    acc_names = set()
    for acc in projects["accounts"]:
        name = acc["name"].lower()
        if name in acc_names:
            errors.append(f"Multiple entries for account name={name}")
        else:
            acc_names.add(name)
        for group in acc.get("project-groups", []):
            if group not in projects["project-groups"].keys():
                errors.append(
                    f"project-group {group} in account {acc['name']} does not exist!"
                )

    for group in acc.get("project-groups", []):
        if set(p["costshare"] for p in group) == {0}:
            errors.append(f"All projects in project-group {group} have costshare=0")

    if raise_on_error and errors:
        raise ValueError(errors)
    return errors


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        projects = yaml.safe_load(f)

    errors = validate(projects)
    if errors:
        print("Configuration is invalid")
        for e in errors:
            print(e)
        sys.exit(2)
    else:
        print("Configuration is valid!")
