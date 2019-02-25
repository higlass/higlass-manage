import click
import subprocess as sp

from higlass_manage.common import hg_name_to_container_name

@click.command()
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
def superuser(hg_name):
    '''
    Create a superuser in the container

    Parameters
    ----------
    hg_name: string
        The name of the container to create a superuser on
    '''
    container_name = hg_name_to_container_name(hg_name)
    sp.run(['docker', 'exec', '-it', container_name, 'python', 'higlass-server/manage.py', 'createsuperuser'])
