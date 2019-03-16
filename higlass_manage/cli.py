import click

from higlass_manage.ingest import ingest
from higlass_manage.list import tilesets, instances
from higlass_manage.start import start
from higlass_manage.stop import stop
from higlass_manage.shell import shell
from higlass_manage.view import view
from higlass_manage.logs import logs

import higlass_manage.create as hmce
import higlass_manage.delete as hmde

@click.group()
def list():
    pass

list.add_command(tilesets)
list.add_command(instances)

@click.group()
def create():
    pass

create.add_command(hmce.superuser)

@click.group()
def delete():
    pass

delete.add_command(hmde.superuser)

@click.group()
def cli():
    pass

cli.add_command(create)
cli.add_command(delete)
cli.add_command(list)
cli.add_command(ingest)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(shell)
cli.add_command(view)
cli.add_command(logs)