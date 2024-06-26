# Experiment: HIC AWS Project Costs

Experimental public repo for processing AWS project costs by tag, taking into account shared AWS accounts.

If this works it may be added to https://github.com/hic-infra/hic-aws-costing-tools and this repo deleted, unless it's excessively complicated in which case this repo will be kept.

## Installation

```
git clone https://github.com/hic-infra/hic-aws-project-costs
cd hic-aws-project-costs
pip install .
```

## Run

You need a configuration file that describes how AWS account costs should be allocated to projects, and a costs CSV generated by https://github.com/hic-infra/hic-aws-costing-tools with arguments:

```
aws-costs --start YYY1-M1-D1 --end YYY2-M2-D2 --granularity monthly --output flat --group1 ACCOUNTNAME --group2 'Proj$'
```

## Limitations

Currently this tool assumes Projects within a single account are distinguished by the `Proj` cost allocation tag.
In future it will be possible to change this tag for individual AWS accounts.
