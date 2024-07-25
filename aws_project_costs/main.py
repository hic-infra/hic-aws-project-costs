import logging
from argparse import ArgumentParser

import yaml

from .project_costs import analyse_costs_csv
from .schema import validate


def main() -> None:
    parser = ArgumentParser("aws-project-costs")
    parser.add_argument(
        "--config", required=True, help="Project costs configuration file"
    )
    parser.add_argument("--costs", required=True, help="Project costs CSV")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    with open(args.config) as f:
        config = yaml.safe_load(f)

    validate(config, raise_on_error=True)
    analyse_costs_csv(config, args.costs, args.output)
