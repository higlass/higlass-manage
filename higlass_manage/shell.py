import click
import docker
import subprocess as sp

from higlass_manage.common import hg_name_to_container_name


@click.command()
@click.option(
    '-n', '--hg_name',
    default='default')
def shell(hg_name):
    '''
    Start a shell in a HiGlass container
    '''
    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    container = client.containers.get(container_name)

    sp.run(['docker', 'exec', '-it', container_name, 'bash'])
