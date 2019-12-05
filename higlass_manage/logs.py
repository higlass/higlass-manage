import click
import os.path as op

from higlass_manage.common import get_data_dir


@click.command()
@click.option(
    '-n', '--hg_name',
    default='default')
def logs(hg_name):
    '''
    Return the error log for a container
    '''
    data_dir = get_data_dir(hg_name)
    log_location = op.join(data_dir, 'log', 'hgs.log')

    with open(log_location, 'r') as f:
        for line in f:
            print(line, end='')
