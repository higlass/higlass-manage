[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1308949.svg)](https://doi.org/10.5281/zenodo.1308949)

# Manage HiGlass Instances

This utility script helps manage local HiGlass instances

## Prerequisites

To use this utility, you will require:

* [Docker](https://www.docker.com/community-edition)
* Python 3

## Installation

`higlass-manage` can be installed using pip

```
pip install higlass-manage
```

## Usage

HiGlass wraps the Docker commands for starting, stopping, listing and populating local higlass instances.

## Tests

To run the tests, first get the test data:

```
./get_test_data.sh
```

And then run the tests:

```
./test.sh
```

### Quickly viewing a dataset

The simplest way to get started is to open and view a dataset. The higlass-manage view command will automatically start a new instance if one isn’t already running, add the given dataset and display it in a browser. Currently, the higlass-manage view command only works with cooler, bigWig, chromsizes and gene-annotation files.

```
wget https://s3.amazonaws.com/pkerp/public/hic-resolutions.cool
higlass-manage view hic-resolutions.cool
```

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

These commands will start an instance running on the default port of 8989. An alternate port can be specified using the ``--port`` parameter. The number of worker processes for the uWSGI application server can be specified with the ``--workers`` parameter.

#### Using the Redis caching service

To make use of the Redis caching service to improve performance, add the `--use-redis` flag. Redis files will be stored by default in the `~/redis-data` directory. Add the `--redis-dir` parameter to override this default.

```
higlass-manage start ... --use-redis --redis-dir /new/path/to/redis-data
```

#### Setting default client options

To the default options for newly created tracks, use the `--default-track-options` parameter to pass in a JSON file containing either
track-specific or general default track options:

```
$cat default_options.json
{
    "all": {
        "showTooltip": "true"
    }
}

$ ./higlass_manage.py start --default-track-options default_options.json
```

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
pete@twok:~/projects/higlass-manage$ higlass-manage list tilesets
VlWKy6ofT6qMFGf-uG_5pQ | beddb | bedlike | GSE93955_CHIP_DMC1_B6_peaks.bed.multires
LAXFhHhASa2zDgJRRS67cw | cooler | matrix | H3K27me3_HiChIP_1.multi.cool
```

### Starting a shell

For debugging purposes it can be useful to run a shell within the Docker container hosting the 
higlass instance. This can accomplished using the `shell` command:

```
higlass-manage shell
```

### Getting the error log

When errors occur they are usually on the higlass-server end. To output the log use the `log` command:

```
higlass-manage log
```

### Stopping a HiGlass instance

To stop a running instance, use the `stop` command:

```
higlass-manage stop
```

## Development

The following is a list of handy commands when developing HiGlass:

- **Start locally built docker image**:
The locally built image must be named `image-default`. Usually built using [higlass-docker](https://github.com/higlass/higlass-docker/). 
   ```
   higlass-manage start --version local
   ```

---

## License

The code in this repository is provided under the MIT License.
