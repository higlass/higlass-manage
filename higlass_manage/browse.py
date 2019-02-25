import click
import docker
import os
import sys
import webbrowser

from higlass_manage.common import get_port

@click.command()
@click.argument('names', nargs=-1)
def browse(names):
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

    # make sure this test passes on Travis CI and doesn't try to open
    # a terminal-based browser which doesn't return
    if not os.environ.get('HAS_JOSH_K_SEAL_OF_APPROVAL'):
        webbrowser.open('http://localhost:{port}/app/'.format(port=port))

