import click
import os.path as op

from higlass_manage.common import get_data_dir

@click.command()
@click.argument('hg_name', nargs=-1)
def logs(hg_name):
    '''
    Return the error log for this container
    '''
    if len(hg_name) == 0:
        hg_name = 'default'
    else:
        hg_name = hg_name[0]

    data_dir = get_data_dir(hg_name)
    log_location = op.join(data_dir, 'log', 'hgs.log')

    with open(log_location, 'r') as f:
        for line in f:
            print(line, end='')