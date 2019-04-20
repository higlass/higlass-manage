import sys
import click
import docker
import json
import requests

from higlass_manage.common import get_port
from higlass_manage.common import CONTAINER_PREFIX, REDIS_PREFIX

@click.command()
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
def tilesets(hg_name):
    '''
    List the datasets in an instance
    '''
    port = get_port(hg_name)

    # use a really high limit to avoid paging
    url = 'http://localhost:{}/api/v1/tilesets/?limit=10000'.format(port)
    ret = requests.get(url)

    if ret.status_code != 200:
        sys.stderr.write('Error retrieving tilesets: {}'.format(ret))
        return

    j = json.loads(ret.content.decode('utf8'))
    for result in j['results']:
        sys.stdout.write("{}\n".format(" | ".join([result['uuid'], result['filetype'], result['datatype'], result['coordSystem'], result['name']])))

@click.command()
def instances():
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
            sys.stdout.write("higlass\t{}\t{}\t{}\n".format(hm_name, directories, port))
        if name.find(REDIS_PREFIX) == 0:
            redis_name = name[len(REDIS_PREFIX)+1:]
            redis_config = client.api.inspect_container(container.name)
            redis_directories = " ".join( ['{}:{}'.format(m['Source'], m['Destination']) for m in redis_config['Mounts']])
            sys.stdout.write("redis\t{}\t{}\t.\n".format(redis_name, redis_directories))

