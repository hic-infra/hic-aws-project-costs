import json
import sys
from pathlib import Path

import jsonschema
import yaml


def validate(projects):
    with (Path(__file__).resolve().parent / "project-cost-schema.json").open() as f:
        schema = json.load(f)

    jsonschema.validate(projects, schema)

    errors = []

    # Check accounts[].project-groups are valid
    for acc in projects["accounts"]:
        for group in acc.get("project-groups", []):
            if group not in projects["project-groups"].keys():
                errors.append(
                    f"project-group {group} in account {acc['name']} does not exist!"
                )
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
