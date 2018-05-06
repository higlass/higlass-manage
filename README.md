# Manage HiGlass Instances

This utility script helps manage local HiGlass instances

## Prerequisites

To use this utility, you will require:

* [Docker](https://www.docker.com/community-edition)
* Python

## Installation

`higlass-manage` can be installed using pip

```
pip install higlass-manage
```

## Usage

HiGlass wraps the Docker commands for starting, stopping, listing and populating local higlass instances.

### Starting a HiGlass instance

Start a local higlass instance using the default data and temporary directories: `~/hg-data` and `/tmp/higlass-docker`. 
All of the data ingested into the instance will be placed into the data directory.

```
higlass-manage.py start
```

### Ingesting data

Use the `ingest` command to add new data. Generally data requires a ``filetype`` and a ``datatype``.
This can sometimes (i.e. in the case of `cooler` and `bigwig` files) be inferred from the file itself.

```
higlass-manage.py ingest my_data.mcool
```

In other, more ambiguous cases, it needs to be explicitly specified:

```
higlass-manage.py ingest my_file.bed --filetype bedfile --datatype bedlike --assembly hg19
```

Note that bedfiles don't store chromosome sizes so they need to be passed in using 
either the `--assembly` or `--chromsizes-filename` parameters.
