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
@click.option(
    "--old-hg-name",
    default="default",
    help="The name of the running higlass container"
         " that needs to be updated.",
    required = False,
)
@click.option(
    "--old-site-url",
    help="site-url at the old location."
         " Provide this when higlass container"
         " one is updating is not running.",
    required=False,
)
@click.option(
    "--old-port",
    help="port at the old location."
         " Provide this when higlass container"
         " one is updating is not running.",
    required=False,
    default="80",
    type=str,
)
@click.option(
    "--old-data-dir",
    help="data directory of the higlass"
         " that is to be updated."
         " typically named 'hg-data'."
         " Provide this when higlass container"
         " is not running.",
    required=False,
)@click.option(
    "--new-site-url",
    default="http://localhost",
    help="site-url at the new location.",
    required=True
)
@click.option(
    "--new-port",
    help="port at the new location",
    required = False,
    default="80",
    type=str,
)
def update_viewconfs(old_hg_name,
                    old_site_url,
                    old_port,
                    old_data_dir,
                    new_site_url,
                    new_port):
    """
    The script allows one to update viewconfs, saved
    in an existing higlass database. It does so
    by modifying references to tillesets that use
    old-site-url:old-port --> new-site-url:new-port

    old/new-site-urls must include schema (http, https):
    http://localhost
    http://old.host.org
    ...

    if 'old-hg-name' is provided and higlass is running,
    then 'old-site-url,old-port,old-data-dir' are inferred.

    if 'old-hg-name' is NOT provided
    then at least 'old-site-url'and 'old-data-dir'
    are required.

    Post 80 is default http port and both
    new-port and old-port defaults to it,
    if not specified otherwise.
    site-url:80 is equivalent to site-url

    Script keeps existing database unchanged,
    but modifies a backed up version "db.sqlite3.updated"
    located in the same path as the original one.

    Running higlass-container would be stopped by
    update_viewconfs.

    """

    # update viewconfs FROM (ORIGIN):
    if old_hg_name is not None:
        # then the container must be running
        try:
            old_site_url = get_site_url(old_hg_name)
            old_port = get_port(old_hg_name)
            old_data_dir = get_data_dir(old_hg_name)
        except docker.errors.NotFound as ex:
            sys.stderr.write(f"Instance not running: {old_hg_name}\n")
    elif (old_site_url is None) or (old_data_dir is None):
        raise ValueError(
            "old-site-url and old-data-dir must be provided,"
            " when instance is not running and no old-hg-name is provided\n"
            )

    # define origin as site_url:port or site_url (when 80)
    origin = old_site_url if (old_port == "80") \
                        else f"{old_site_url}:{old_port}"

    # update viewconfs TO (DESTINATION):
    # define destination as site_url:port or site_url (when 80)
    destination = new_site_url if (new_port == "80") \
                        else f"{new_site_url}:{new_port}"

    # locate db.sqlite3 and name for the updated version:
    origin_db_path = op.join(old_data_dir, _SQLITEDB)
    update_db_path = op.join(old_data_dir, f"{_SQLITEDB}.updated")

    # to be continued

    # stop the container before backup:
    sys.stderr.write(
        f"Stopping running higlass-container {old_hg_name} ...\n"
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
