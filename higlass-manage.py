#!/usr/bin/python

import argparse
import click
import os.path as op
import subprocess as sp
import sys
import webbrowser

@click.group()
def cli():
    pass

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
        default=None,
        help='The version of the Docker container to use',
        type=str)
@click.option('-p', '--port',
        default=8989,
        help='The port that the HiGlass instance should run on',
        type=str)
def start(temp_dir, data_dir, version, port):
    version_addition = '' if version is None else ':{}'.format(version)

    # try to stop and remove currently running images
    ret = sp.call(['docker', 'stop', 
        'higlass-container'.format(version_addition)])
    ret = sp.call(['docker', 'rm', 
        'higlass-container'.format(version_addition)])

    ret = sp.call(['docker', 'pull', 
        'gehlenborglab/higlass{}'.format(version_addition)])

    if ret != 0:
        print("Error pulling latest Docker image", file=sys.stderr)
        return

    print('ret:', ret)

    sp.call(['docker', 'run', '--detach',
        '--publish', str(port) + ':80',
        '--volume', op.expanduser(temp_dir) + ':/tmp',
        '--volume', op.expanduser(data_dir) + ':/data',
        '--name', 'higlass-container',
        'gehlenborglab/higlass'])
    
    webbrowser.open('http://localhost:{port}/'.format(port=port))
    pass

@cli.command()
@click.option(argument)
def ingest(filename):
    pass

def main():
    parser = argparse.ArgumentParser(description="""
    
    python higlass-manage.py [start/ingest]

    Manage local higlass instances
""")
    cli(obj={})

if __name__ == '__main__':
    main()


