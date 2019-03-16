import click
import docker

from .common import CONTAINER_PREFIX

@click.command()
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
