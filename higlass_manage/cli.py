import click

from higlass_manage import __version__
from higlass_manage.ingest import ingest
from higlass_manage.list import tilesets, instances
from higlass_manage.start import start
from higlass_manage.stop import stop
from higlass_manage.shell import shell
from higlass_manage.view import view
from higlass_manage.logs import logs
from higlass_manage.create import superuser as create_superuser
from higlass_manage.delete import superuser as delete_superuser


@click.group()
def list():
    """
    List instances or datasets
    """


list.add_command(tilesets)
list.add_command(instances)


@click.group()
def create():
    pass


create.add_command(create_superuser)


@click.group()
def delete():
    pass


delete.add_command(delete_superuser)


@click.version_option(__version__, "-V", "--version")
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
