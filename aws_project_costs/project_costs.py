import json
from enum import Enum
from operator import itemgetter
from typing import Any, Hashable, Optional

import pandas as pd

PROJECT_TAG = "Proj"


class CostSourceType(Enum):
    PROJECT_SPECIFIC = "project"
    SHARED = "shared"


def _get_account_cfg(config: dict[str, Any], accountname: str) -> dict[str, Any]:
    for acc in config["accounts"]:
        if acc["name"].lower() == accountname.lower():
            return acc
    raise ValueError(f"Configuration for account {accountname} not found")


def _get_project_costshares_in_groups(
    config: dict[str, Any], groupnames: list[str]
) -> dict[str, int]:
    """
    Get the combined set of all projects in groupnames, and their costshare
    If a project is in multiple groups it must have the same costshare
    """
    projects: dict[str, int] = dict()
    for group in groupnames:
        for p in config["project-groups"][group]:
            name = p["name"]
            costshare = p["costshare"]
            if name in projects and costshare != projects[name]:
                raise ValueError(
                    f"Project {name} appears in multiple project groups"
                    f"{groupnames} but has different costshares"
                )
            projects[name] = costshare
    return projects


def _project_specific_account(
    start: pd.Timestamp,
    description: str,
    project_name: str,
    costs_dict: list[dict[Hashable, Any]],
) -> list[tuple[str, str, str, Any, str, Any]]:
    rows = []

    for item in costs_dict:
        costs_tag = item[f"{PROJECT_TAG}$"]
        rows.append(
            (
                start.date().isoformat(),
                project_name,
                description,
                costs_tag,
                CostSourceType.PROJECT_SPECIFIC.value,
                item["COST"],
            )
        )
    return rows


def _shared_account(
    start: pd.Timestamp,
    description: str,
    proj_tag_names_map: dict[str, str],
    shared_tag_values: list[str],
    project_tagname: Optional[str],
    projects_in_group: dict[str, int],
    costs_dict: list[dict[Hashable, Any]],
) -> list[tuple[str, str, str, Any, str, Any]]:
    rows = []

    for item in costs_dict:
        costs_tag = item[f"{PROJECT_TAG}$"]
        if not costs_tag.startswith(f"{PROJECT_TAG}$"):
            raise NotImplementedError(f"Project tag {costs_tag} not yet implemented")

        project_tag = costs_tag[5:]
        if project_tagname and project_tag and (project_tag not in shared_tag_values):
            if project_tag not in proj_tag_names_map:
                raise ValueError(f"{project_tag} is not in proj-tag-names")
            project_name = proj_tag_names_map[project_tag]
            rows.append(
                (
                    start.date().isoformat(),
                    project_name,
                    description,
                    costs_tag,
                    CostSourceType.PROJECT_SPECIFIC.value,
                    item["COST"],
                )
            )
        else:
            # Either untagged, or a tag that should be considered shared
            total_costshare = sum(projects_in_group.values())
            cost_per_share = item["COST"] / total_costshare
            for project_name in projects_in_group:
                rows.append(
                    (
                        start.date().isoformat(),
                        project_name,
                        description,
                        costs_tag,
                        CostSourceType.SHARED.value,
                        cost_per_share * projects_in_group[project_name],
                    )
                )
    return rows


def allocate_costs(
    *, accountname: str, config: dict[str, Any], start: pd.Timestamp, df: pd.DataFrame
) -> list[tuple[str, str, str, Any, str, Any]]:
    account_cfg = _get_account_cfg(config, accountname)

    costs = df[(df["START"] == start) & (df["accountname"] == accountname)]
    billing_type = account_cfg["billing-type"]

    costs_dict = costs.to_dict(orient="records")
    description = f"{accountname} [{billing_type}]"

    if billing_type == "project-specific":
        project_name = account_cfg["project"]
        rows = _project_specific_account(
            start,
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

        projects_in_group = _get_project_costshares_in_groups(
            config, account_cfg["project-groups"]
        )
        rows = _shared_account(
            start,
            description,
            config["proj-tag-names"],
            config["shared-tag-values"],
            project_tagname,
            projects_in_group,
            costs_dict,
        )

    else:
        raise ValueError(f"Invalid billing-type {billing_type}")

    # [(start, project name, account, source, source type, cost)]
    return rows


def analyse_costs_csv(
    config: dict[str, Any],
    costs_csv_filename: str,
    output_csv_filename: Optional[str] = None,
) -> None:
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
            itemised_rows,
            columns=["start", "projectname", "account", "tag", "sourcetype", "cost"],
        )
        out.to_csv(output_csv_filename, index=False)
    else:
        print(json.dumps(itemised_rows, indent=2))
