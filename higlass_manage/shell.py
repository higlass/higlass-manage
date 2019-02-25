import click
import docker
import subprocess as sp

from higlass_manage.common import hg_name_to_container_name

@click.command()
@click.argument('hg-name', nargs=-1)
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
    