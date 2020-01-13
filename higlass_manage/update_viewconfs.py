import sys
import click
import os.path as op
import sqlite3
import shutil

from higlass_manage.common import get_data_dir, \
                                  get_site_url, \
                                  get_port

_SQLITEDB = "db.sqlite3"

def _stop(name):
    import docker
    from higlass_manage.common import CONTAINER_PREFIX
    client = docker.from_env()
    # higlass container
    hm_name = "{}-{}".format(CONTAINER_PREFIX, name)
    try:
        client.containers.get(hm_name).stop()
        # client.containers.get(hm_name).remove()
    except docker.errors.NotFound as ex:
        sys.stderr.write("Instance not running: {}\n".format(name))


@click.command()
# @click.argument("hg_name", nargs=-1)
@click.option(
    "--hg-name",
    default="default",
    help="The name of the running-higlass container to migrate",
)
@click.option(
    "--destination-site",
    default="http://localhost",
    help="site-url at the destination of migration",
    required=True,
    # perhaps use click to check if it's a url
)
@click.option(
    "--destination-port",
    help="port at the destination of migration",
    required = False,
    # should this be str or int - 80 or "" ...
)
@click.option(
    "--origin-site",
    help="site-url at the origin of migration."
         " If not provided: the script will calculate"
         " it from the running higlass-container",
    required=False,
    # perhaps use click to check if it's a url
)
@click.option(
    "--origin-port",
    help="port at the origin of migration."
         " If not provided: the script will calculate"
         " it from the running higlass-container",
    required=False,
    # perhaps use click to check if it is an int with range
)
@click.option(
    "--data-dir",
    help="The higlass data directory to look"
         " db.sqlite3 database file.",
    required=False,
)
def update_viewconfs(hg_name,
                    destination_site,
                    destination_port,
                    origin_site,
                    origin_port,
                    data_dir):
    """
    Prepare database of a given higlass
    container for migration.

    Backup current database.
    Create a new version of the database,
    where URLs of current tileset are going
    to be replace with the user-provided
    destination URL.

    (relevant for keeping existing viewconf
    functional after migration, might be
    important for other items).
    """

    # ORIGIN and --data-dir:
    if hg_name is not None:
        # then the container must be running
        try:
            origin_site = get_site_url(hg_name)
            origin_port = get_port(hg_name)
            data_dir = get_data_dir(hg_name)
        except docker.errors.NotFound as ex:
            sys.stderr.write("Instance not running: {}\n".format(hg_name))
    elif (origin_site is None) or (data_dir is None):
        raise ValueError(
            "origin-site and data-dir must be provided, when instance is not running\n"
            )

    origin_port = "80" if (origin_port is None) else str(origin_port)
    # define origin as site_url:port or site_url (when 80)
    origin = origin_site if (origin_port == "80") \
                        else f"{origin_site}:{origin_port}"

    # DESTINATION:
    if destination_port is None:
        sys.stderr.write("destination port was not set, using 80 ...\n")
        sys.stderr.flush()
        destination_port = "80"
    # define destination as site_url:port or site_url (when 80)
    destination = destination_site if (destination_port == "80") \
                        else f"{destination_site}:{destination_port}"

    # locate db.sqlite3 and name for its backup:
    db_location = op.join(data_dir, _SQLITEDB)
    db_backup = op.join(data_dir, f"{_SQLITEDB}.backup")

    # stop the container before backup:
    sys.stderr.write(
        "Stopping running higlass-container {} ...\n".format(hg_name)
        )
    sys.stderr.flush()
    _stop(hg_name)
    # hopefully db_location is not in use now ...
    shutil.copyfile(db_location, db_backup)


    # once db_backup is done, we can connect to the DB
    conn = None
    try:
        conn = sqlite3.connect(db_backup)
    except Error as e:
        print(e)

    sql = '''UPDATE tilesets_viewconf
             SET viewconf = replace(viewconf,
                     '{_origin}',
                     '{_destination}')
          '''.format(_origin = origin,
                     _destination = destination)

    # we probably need to add some reporting ...
    # how many entries were replaced, etc
    # should look some place other than "viewconf" table ?!

    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()


    sys.stderr.write(
        "DB is ready for migration, just copy db.backup"
        "along with the ./media to new destination ...\n"
        )
    sys.stderr.flush()
