import sys
import click
import docker

from .common import CONTAINER_PREFIX, NETWORK_PREFIX, REDIS_PREFIX

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
        # higlass container
        hm_name = '{}-{}'.format(CONTAINER_PREFIX, name)
        try:
            client.containers.get(hm_name).stop()
            client.containers.get(hm_name).remove()
        except docker.errors.NotFound as ex:
            sys.stderr.write("Instance not running: {}\n".format(name))
            
        # redis container
        redis_name = '{}-{}'.format(REDIS_PREFIX, name)
        try:
            client.containers.get(redis_name).stop()
            client.containers.get(redis_name).remove()
        except docker.errors.NotFound:
            sys.stderr.write("No Redis instances found at {}; skipping...\n".format(redis_name))
            
        # bridge network
        network_name = '{}-{}'.format(NETWORK_PREFIX, name)
        try:
            network_list = client.networks.list(names=[network_name])
            if network_list:
                network = client.networks.get(network_name)
                network.remove()
        except docker.errors.NotFound:
            sys.stderr.write("No bridge network found at {}; skipping...\n".format(network_name))
        
