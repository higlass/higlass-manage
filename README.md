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
All of the data ingested into the instance will be placed into the data directory. Alternate data and temp directory can be specified using ``--data-dir`` and ``--temp-dir`` parameters.

```
higlass-manage start
```

If you want to make your instance accessible to the outside world, you need to specify the host URL that it will be available through using the `--site-url` parameter:

```
higlass-manage start --site-url higlass.io
```

These commands will start an instance running on the default port of 8989. An alternate port can be specified using the ``--port`` parameter.

### Ingesting data

Use the `ingest` command to add new data. Generally data requires a ``filetype`` and a ``datatype``.
This can sometimes (i.e. in the case of `cooler` and `bigwig` files) be inferred from the file itself.

```
higlass-manage ingest my_data.mcool
```

In other, more ambiguous cases, it needs to be explicitly specified:

```
higlass-manage ingest my_file.bed --filetype bedfile --datatype bedlike --assembly hg19
```

Note that bedfiles don't store chromosome sizes so they need to be passed in using 
either the `--assembly` or `--chromsizes-filename` parameters.

### Listing available datasets

```
pete@twok:~/projects/higlass-manage$ higlass-manage list_data
VlWKy6ofT6qMFGf-uG_5pQ | beddb | bedlike | GSE93955_CHIP_DMC1_B6_peaks.bed.multires
LAXFhHhASa2zDgJRRS67cw | cooler | matrix | H3K27me3_HiChIP_1.multi.cool
```

### Stopping a HiGlass instance

To stop a running instance, use the `stop` command:

```
higlass-manage stop
```

