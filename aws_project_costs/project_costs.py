import json
from operator import itemgetter

import pandas as pd

PROJECT_TAG = "Proj"


def _get_account_cfg(config, accountname):
    for acc in config["accounts"]:
        if acc["name"].lower() == accountname.lower():
            return acc
    raise ValueError(f"Configuration for account {accountname} not found")


def _get_projects_in_groups(config, groupnames):
    projects = set()
    for group in groupnames:
        projects.update(config["project-groups"][group])
    return projects


def _project_specific_account(description, project_name, costs_dict):
    rows = []

    for item in costs_dict:
        costs_tag = item[f"{PROJECT_TAG}$"]
        rows.append((project_name, description, costs_tag, item["COST"]))
    return rows


def _shared_account(
    description, proj_tag_names_map, project_tagname, projects_in_group, costs_dict
):
    rows = []

    for item in costs_dict:
        costs_tag = item[f"{PROJECT_TAG}$"]
        if not costs_tag.startswith(f"{PROJECT_TAG}$"):
            raise NotImplementedError(f"Project tag {costs_tag} not yet implemented")

        project_tag = costs_tag[5:]
        if project_tagname and project_tag:
            project_name = proj_tag_names_map[project_tag]
            rows.append((project_name, description, costs_tag, item["COST"]))
        else:
            cost_per_project = item["COST"] / len(projects_in_group)
            for project_name in projects_in_group:
                rows.append((project_name, description, costs_tag, cost_per_project))
    return rows


def allocate_costs(*, accountname, config, start, df):
    account_cfg = _get_account_cfg(config, accountname)

    costs = df[(df["START"] == start) & (df["accountname"] == accountname)]
    billing_type = account_cfg["billing-type"]

    costs_dict = costs.to_dict(orient="records")
    description = f"{accountname} [{billing_type}]"

    if billing_type == "project-specific":
        project_name = account_cfg["project"]
        rows = _project_specific_account(
            description,
            project_name,
            costs_dict,
        )

    elif billing_type == "shared":
        project_tagname = account_cfg.get("project-tagname")
        if project_tagname and project_tagname != PROJECT_TAG:
            raise NotImplementedError(
                f"Project tag {project_tagname} not yet implemented"
            )

        projects_in_group = _get_projects_in_groups(
            config, account_cfg["project-groups"]
        )
        rows = _shared_account(
            description,
            config["proj-tag-names"],
            project_tagname,
            projects_in_group,
            costs_dict,
        )

    else:
        raise ValueError(f"Invalid billing-type {billing_type}")

    # [(project name, account, source, cost)]
    return rows


def analyse_costs_csv(config, costs_csv_filename, output_csv_filename=None):
    df = pd.read_csv(
        costs_csv_filename,
        dtype={"accountname": str, f"{PROJECT_TAG}$": str, "COST": float},
        parse_dates=["START", "END"],
        date_format="ISO8601",
    )

    itemised_rows = []

    for start in sorted(df["START"].unique()):
        month_costs = df[df["START"] == start]
        for accountname in month_costs["accountname"].unique():
            # print(f"Processing {accountname} {start}")
            try:
                acc_itemised_rows = allocate_costs(
                    accountname=accountname,
                    config=config,
                    start=start,
                    df=df,
                )
                itemised_rows.extend(sorted(acc_itemised_rows, key=itemgetter(1, 2, 0)))
            except Exception as e:
                print(f"ERROR: Failed to analyse account {accountname} {start} {e}")
                raise

    if output_csv_filename:
        out = pd.DataFrame(
            itemised_rows, columns=["projectname", "account", "tag", "cost"]
        )
        out.to_csv(output_csv_filename, index=False)
    else:
        print(json.dumps(itemised_rows, indent=2))
