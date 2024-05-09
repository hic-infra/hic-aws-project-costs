import json
import sys
from pathlib import Path

import jsonschema
import yaml

with open(sys.argv[1]) as f:
    projects = yaml.safe_load(f)

with (Path(__file__).resolve().parent / "project-cost-schema.json").open() as f:
    schema = json.load(f)

jsonschema.validate(projects, schema)

ok = True

# Check accounts[].project-groups are valid
for acc in projects["accounts"]:
    for group in acc.get("project-groups", []):
        if group not in projects["project-groups"].keys():
            print(f"project-group {group} in account {acc['name']} does not exist!")
            ok = False

if ok:
    print("Schema is valid!")
