import sys
import click
import os.path as op
import sqlite3
import shutil
import docker

from .common import (
    get_data_dir,
    get_site_url,
    get_port,
    hg_name_to_container_name,
    SQLITEDB,
)

from .stop import _stop


@click.command()
@click.option(
    "--old-hg-name",
    help="The name of the running higlass container that needs to be updated.",
    required=False,
)
@click.option(
    "--old-site-url",
    help="site-url at the old location."
    " Provide this when higlass container"
    " to be updated is not running.",
    required=False,
)
@click.option(
    "--old-port",
    help="port at the old location."
    " Provide this when higlass container"
    " to be updated is not running.",
    required=False,
    default="80",
    type=str,
)
@click.option(
    "--old-data-dir",
    help="data directory of the higlass"
    " that is to be updated (usually 'hg-data')."
    " Provide this when higlass container"
    " is not running.",
    required=False,
)
@click.option(
    "--new-site-url",
    default="http://localhost",
    help="site-url at the new location.",
    required=True,
)
@click.option(
    "--new-port",
    help="port at the new location",
    required=False,
    default="80",
    type=str,
)
@click.option(
    "--db-backup-name",
    help="name of the database (db) backup file."
    " db backup will be stored in the data directory"
    " provided explicitly or inferred from the running"
    " container.",
    required=False,
    default=f"{SQLITEDB}.updated",
    type=str,
)
def update_viewconfs(
    old_hg_name,
    old_site_url,
    old_port,
    old_data_dir,
    new_site_url,
    new_port,
    db_backup_name,
):
    """Update stored viewconfs from one host to another

    The script allows one to update viewconfs saved
    in an existing higlass database. It does so
    by modifying references to tilesets that use
    old-site-url:old-port --> new-site-url:new-port

    old/new-site-urls must include schema (http, https):
    http://localhost
    http://old.host.org
    ...

    if 'old-hg-name' is provided and higlass is running,
    then 'old-site-url,old-port,old-data-dir' are inferred.

    if 'old-hg-name' is NOT provided
    then at least 'old-site-url'and 'old-data-dir'
    are required. This scenario should be invoked
    only when the container is not running, otherwise
    integrity of the DB-backup can not be guaranteed.

    Post 80 is default http port and both
    new-port and old-port defaults to it,
    if not specified otherwise.
    site-url:80 is equivalent to site-url

    Script keeps existing database unchanged,
    but modifies a backed up version located
    in the same path as the original one.

    Running higlass-container would be interrupted
    during database backup.

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
    origin = old_site_url if (old_port == "80") else f"{old_site_url}:{old_port}"

    # update viewconfs TO (DESTINATION):
    # define destination as site_url:port or site_url (when 80)
    destination = new_site_url if (new_port == "80") else f"{new_site_url}:{new_port}"

    # locate db.sqlite3 and name for the updated version:
    origin_db_path = op.join(old_data_dir, SQLITEDB)
    update_db_path = op.join(old_data_dir, db_backup_name)

    # backup the database using simple copyfile, stop container before
    if old_hg_name is not None:
        _stop([old_hg_name,], False, False, False)
    try:
        shutil.copyfile(origin_db_path, update_db_path)
    except (OSError, IOError):
        sys.stderr.write(f"Failed to copy {origin_db_path} to {update_db_path}")
        sys.exit(-1)
    finally:
        # restart container even if exception occurs:
        if old_hg_name is not None:
            sys.stderr.write(f"Restarting container {old_hg_name} ...\n")
            sys.stderr.flush()
            client = docker.from_env()
            container_name = hg_name_to_container_name(old_hg_name)
            client.containers.get(container_name).restart()
    # alternatively database could be backed up using a "backup"-mechanism:
    # CLI
    #    res = subprocess.run(["sqlite3", origin_db_path, f".backup {update_db_path}"])
    # Python API >= 3.7.0
    #       conn = sqlite3.connect(origin_db_path)
    #       conn.backup(update_db_path)
    # check if it is indeed "atomic" and can be done on a "live" database .

    # now modify the backed-up database "update_db_path" using sqlite3 API:
    conn = None
    try:
        conn = sqlite3.connect(update_db_path)
    except sqlite3.Error as e:
        sys.stderr.write(f"Failed to connect to {update_db_path}\n")
        sys.exit(-1)

    # sql query to update viewconfs, by replacing origin -> destination
    db_query = f"""
            UPDATE tilesets_viewconf
            SET viewconf = replace(viewconf,'{origin}','{destination}')
            """
    # exec sql query
    with conn:
        cur = conn.cursor()
        cur.execute(db_query)

    conn.close()
    # todo: add some stats on - how many viewconfs
    # were updated

    sys.stderr.write(
        f"Backed up version of the database {update_db_path}\n"
        " has been updated and ready for migration\n\n"
        " copy it to the new host along with the media folder\n"
        f" rename the database file back to {SQLITEDB} and restart higlass.\n"
    )
    sys.stderr.flush()
    sys.exit(0)
