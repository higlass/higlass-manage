#!/usr/bin/python

import argparse
import click
import clodius.cli.aggregate as cca
import clodius.chromosomes as cch
import docker
import json
import os
import os.path as op
import requests
import subprocess as sp
import sys
import tempfile
import webbrowser

CONTAINER_PREFIX = 'higlass-manage-container'

def hg_name_to_container_name(hg_name):
    return '{}-{}'.format(CONTAINER_PREFIX, hg_name)

@click.group()
def cli():
    pass

def aggregate_file(filename, filetype, assembly, chromsizes_filename, has_header):
    if filetype == 'bedfile':
        if assembly is None and chromsizes_filename is None:
            print('An assembly or set of chromosome sizes is required when importing bed files. Please specify one or the other using the --assembly or --chromsizes-filename parameters', file=sys.stderr)
            return

        with tempfile.TemporaryDirectory() as td:
            output_file = op.join(td, filename + '.beddb')

            print("Aggregating bedfile")
            cca._bedfile(filename,
                    output_file,
                    assembly,
                    importance_column='random',
                    has_header=has_header,
                    chromosome=None,
                    max_per_tile=50,
                    delimiter=None,
                    chromsizes_filename=chromsizes_filename,
                    offset=0,
                    tile_size=1024)

            to_import = output_file

            # because we aggregated the file, the new filetype is beddb
            filetype='beddb'
            return (to_import, filetype)
    elif filetype == 'bedpe':
        if assembly is None and chromsizes_filename is None:
            print('An assembly or set of chromosome sizes is required when importing bed files. Please specify one or the other using the --assembly or --chromsizes-filename parameters', file=sys.stderr)
            return

        with tempfile.TemporaryDirectory() as td:
            output_file = op.join(td, filename + '.beddb')

            print("Aggregating bedfile")
            cca._bedpe(filename,
                    output_file,
                    assembly,
                    importance_column='random',
                    has_header=has_header,
                    chromosome=None,
                    max_per_tile=50,
                    chromsizes_filename=chromsizes_filename,
                    tile_size=1024)

            to_import = output_file

            # because we aggregated the file, the new filetype is beddb
            filetype='bed2ddb'
            return (to_import, filetype)
    else:
        return (filename, filetype)


def import_file(hg_name, filepath, filetype, datatype, assembly):
    # get this container's temporary directory
    temp_dir = get_temp_dir(hg_name)
    if not op.exists(temp_dir):
        os.makedirs(temp_dir)
        
    filename = op.split(filepath)[1]
    to_import_path = op.join(temp_dir, filename)

    if to_import_path != filepath:
        # if this file already exists in the temporary dir
        # remove it
        if op.exists(to_import_path):
            print("Removing existing file in temporary dir:", to_import_path)
            os.remove(to_import_path)

        os.link(filepath, to_import_path)

    coordSystem = '--coordSystem {}'.format(assembly) if assembly is not None else ''

    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    container = client.containers.get(container_name)

    (exit_code, output) = container.exec_run( 'python higlass-server/manage.py ingest_tileset --filename' +
            ' /tmp/{}'.format(filename) +
            ' --filetype {} --datatype {} {}'.format(
                filetype, datatype, coordSystem))
    print('exit_code:', exit_code)
    print('output:', output)

    pass

def get_temp_dir(hg_name):
    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)

    for mount in config['Mounts']:
        if mount['Destination'] == '/tmp':
            return mount['Source']

def get_data_dir(hg_name):
    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)

    for mount in config['Mounts']:
        if mount['Destination'] == '/data':
            return mount['Source']

def get_port(hg_name):
    client = docker.from_env()

    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)
    port = config['HostConfig']['PortBindings']['80/tcp'][0]['HostPort']

    return port

def infer_filetype(filename):
    _,ext = op.splitext(filename)

    if ext.lower() == '.bw' or ext.lower() == '.bigwig':
        return 'bigwig'
    elif ext.lower() == '.mcool' or ext.lower() == '.cool':
        return 'cooler'
    elif ext.lower() == '.htime':
        return 'time-interval-json'
    elif ext.lower() == '.hitile':
        return 'hitile'

    return None

def infer_datatype(filetype):
    if filetype == 'cooler':
        return 'matrix'
    if filetype == 'bigwig':
        return 'vector'
    if filetype == 'time-interval-json':
        return 'time-interval'
    if filetype == 'hitile':
        return 'vector'

def recommend_filetype(filename):
    ext = op.splitext(filename)
    if op.splitext(filename)[1] == '.bed':
        return 'bedfile'
    if op.splitext(filename)[1] == '.bedpe':
        return 'bedpe'

def recommend_datatype(filetype):
    if filetype == 'bedfile':
        return 'bedlike'

def get_hm_config():
    '''
    Return the config file for the currently set up instances.
    '''
    hm_config_filename = op.expanduser('~/.higlass-manage')

    try:
        with open(hm_config_filename, 'r') as f:
            hm_config_json = json.load(f)
    except FileNotFoundError as fnfe:
        print("No existing config file found, returning an empty config", file = sys.stderr)
        # config file not found, return an empty config
        return {}

def update_hm_config(hm_config):
    '''
    Update the hm_config on disk
    '''
    try:
        with open(hm_config_filename, 'w') as f:
            json.write(f, hm_config)
    except Exception as ex:
        print("Error updating the hm_config: {}".format(ex))

@cli.command()
@click.option('-t', '--temp-dir',
        default='/tmp/higlass-docker',
        help='The temp directory to use',
        type=str)
@click.option('-d', '--data-dir',
        default='~/hg-data',
        help='The higlass data directory to use',
        type=str)
@click.option('-v', '--version',
        default='latest',
        help='The version of the Docker container to use',
        type=str)
@click.option('-p', '--port',
        default=8989,
        help='The port that the HiGlass instance should run on',
        type=str)
@click.option('-n', '--name',
        default='default',
        help='The name for this higlass instance',
        type=str)
@click.option('-s', '--site-url',
        default=None,
        help='When creating an external-facing instance, enter its IP or hostname using this parameter',
        type=str)
def start(temp_dir, data_dir, version, port, name, site_url):
    '''
    Start a HiGlass instance
    '''
    container_name = '{}-{}'.format(CONTAINER_PREFIX,name)

    client = docker.from_env()

    try:
        container = client.containers.get(container_name)

        print('Stopping previously running container')
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        # container isn't running so no need to stop it
        pass

    if version == 'local':
        image = client.images.get('image-default')
    else:
        image = client.images.pull('gehlenborglab/higlass', version)

    data_dir = op.expanduser(data_dir)
    temp_dir = op.expanduser(temp_dir)

    if not op.exists(temp_dir):
        os.makedirs(temp_dir)
    if not op.exists(data_dir):
        os.makedirs(data_dir)

    environment = {}

    if site_url is not None:
        environment['SITE_URL'] = site_url

    print('Data directory:', data_dir)
    print('Temp directory:', temp_dir)

    version_addition = '' if version is None else ':{}'.format(version)

    print('Starting...', name, port)
    client.containers.run(image,
            ports={80 : port},
            volumes={
                temp_dir : { 'bind' : '/tmp', 'mode' : 'rw' },
                data_dir : { 'bind' : '/data', 'mode' : 'rw' }
                },
            name=container_name,
            environment=environment,
            detach=True)
    print('Docker started: {}'.format(container_name))

    return

    sp.call(['docker', 'run', '--detach',
        '--publish', str(port) + ':80',
        '--volume', temp_dir + ':/tmp',
        '--volume', data_dir + ':/data',
        '--name', 'higlass-container',
        'gehlenborglab/higlass'])
    
    webbrowser.open('http://localhost:{port}/app'.format(port=port))
    pass

@cli.command()
def list():
    '''
    List running instances
    '''
    client = docker.from_env()

    for container in client.containers.list():
        name = container.name
        if name.find(CONTAINER_PREFIX) == 0:
            hm_name = name[len(CONTAINER_PREFIX)+1:]
            config = client.api.inspect_container(container.name)
            directories = " ".join( ['{}:{}'.format(m['Source'], m['Destination']) for m in  config['Mounts']])
            port = config['HostConfig']['PortBindings']['80/tcp'][0]['HostPort']
            print(hm_name, "{} {}".format(directories, port))

@cli.command()
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
def list_data(hg_name):
    '''
    List the datasets in an instance
    '''
    port = get_port(hg_name)

    # use a really high limit to avoid paging
    url = 'http://localhost:{}/api/v1/tilesets/?limit=10000'.format(port)
    ret = requests.get(url)

    if ret.status_code != 200:
        print('Error retrieving tilesets:', ret)
        return

    j = json.loads(ret.content.decode('utf8'))
    for result in j['results']:
        print(" | ".join([result['uuid'], result['filetype'], result['datatype'], result['name']]))

@cli.command()
@click.argument('names', nargs=-1)
def browser(names):
    '''
    Launch a web browser for a running instance
    '''
    client = docker.from_env()

    if len(names) == 0:
        names = ('default',)

    try:
        port = get_port(names[0])
    except docker.errors.NotFound:
        print("Error: higlass instance not found. Have you tried starting it using 'higlass-manage start'?", file=sys.stderr)
        return

    webbrowser.open('http://localhost:{port}/app/'.format(port=port))

@cli.command()
@click.argument('names', nargs=-1)
def stop(names):
    '''
    Stop a running instance
    '''
    client = docker.from_env()

    if len(names) == 0:
        names = ('default',)

    for name in names:
        hm_name = '{}-{}'.format(CONTAINER_PREFIX, name)

        try:
            client.containers.get(hm_name).stop()
            client.containers.get(hm_name).remove()
        except docker.errors.NotFound as ex:
            print("Instance not running: {}".format(name))

@cli.command()
@click.argument('filename')
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
@click.option('--filetype', default=None, help="The type of file to ingest (e.g. cooler)")
@click.option('--datatype', default=None, help="The data type of in the input file (e.g. matrix)")
@click.option('--assembly', default=None, help="The assembly that this data is mapped to")
@click.option('--chromsizes-filename', default=None, help="A set of chromosome sizes to use for bed and bedpe files")
@click.option('--has-header', default=False, is_flag=True, help="Does the input file have column header information (only relevant for bed or bedpe files)")
def ingest(filename, hg_name, filetype, datatype, assembly, chromsizes_filename, has_header):
    '''
    Ingest a dataset
    '''
    if not op.exists(filename):
        print('File not found:', filename, file=sys.stderr)
        return

    if filetype is None:
        # no filetype provided, try a few common filetypes
        filetype = infer_filetype(filename)
        print('Inferred filetype:', filetype)

        if filetype is None:
            recommended_filetype = recommend_filetype(filename)

            print('Unknown filetype, please specify using the --filetype option', file=sys.stderr)
            if recommended_filetype is not None:
                print("Based on the filename, you may want to try the filetype: {}".format(recommended_filetype))
            
            return

    if datatype is None:
        datatype = infer_datatype(filetype)
        print('Inferred datatype:', datatype)

        if datatype is None:
            recommended_datatype = recommend_datatype(filetype)
            print('Unknown datatype, please specify using the --datatype option', file=sys.stderr)
            if recommended_datatype is not None:
                print("Based on the filetype, you may want to try the datatype: {}".format(recommended_datatype))



    (to_import, filetype) = aggregate_file(filename, filetype, assembly, chromsizes_filename, has_header)
    import_file(hg_name, to_import, filetype, datatype, assembly)


@cli.command()
@click.argument('hg_name', nargs=-1)
def shell(hg_name):
    '''
    Start a shell in a higlass container
    '''
    if len(hg_name) == 0:
        hg_name = 'default'
    else:
        hg_name = hg_name[0]

    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    container = client.containers.get(container_name)

    sp.run(['docker', 'exec', '-it', container_name, 'bash'])
    

@cli.command()
@click.argument('hg_name', nargs=-1)
def log(hg_name):
    '''
    Return the error log for this container
    '''
    if len(hg_name) == 0:
        hg_name = 'default'
    else:
        hg_name = hg_name[0]

    data_dir = get_data_dir(hg_name)
    log_location = op.join(data_dir, 'log', 'hgs.log')

    with open(log_location, 'r') as f:
        for line in f:
            print(line, end='')

def main():
    parser = argparse.ArgumentParser(description="""
    
    python higlass-manage.py [start/ingest]

    Manage local higlass instances
""")
    cli(obj={})

if __name__ == '__main__':
    main()


