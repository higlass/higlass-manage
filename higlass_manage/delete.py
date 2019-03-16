import click
import subprocess as sp

from higlass_manage.common import hg_name_to_container_name

@click.command()
@click.argument('username')
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
def superuser(username, hg_name):
    '''
    Delete a superuser in the container

    Parameters
    ----------
    hg_name: string
        The name of the container to create a superuser on
    '''
    container_name = hg_name_to_container_name(hg_name)
    proc_input = 'from django.contrib.auth.models import User; User.objects.get(username="{}").delete()'.format(username)
    sp.run(['docker', 'exec', '-i', container_name, 'python', 'higlass-server/manage.py', 'shell'], input=proc_input.encode('utf8'))