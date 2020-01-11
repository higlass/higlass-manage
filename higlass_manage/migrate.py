import sys
import click
import os.path as op
import sqlite3

from higlass_manage.common import get_data_dir, \
                                  get_site_url, \
                                  get_port

_SQLITEDB = "db.sqlite3"

@click.command()
@click.argument("hg_name", nargs=-1)
# @click.option(
#     "--hg-name",
#     default="default",
#     help="The name of the higlass container to migrate",
# )
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
def migrate(hg_name,
            destination_site,
            destination_port,
            origin_site,
            origin_port):
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

    if len(hg_name) == 0:
        hg_name = "default"
    else:
        hg_name = hg_name[0]

    # ORIGIN:
    # first, while higlass `hg_name` is running
    # or available - figure out its current site_url
    if origin_site is None:
        origin_site = get_site_url(hg_name)
    # same for port
    if origin_port is None:
        origin_port = get_port(hg_name)
    # define origin as site_url:port or site_url (when 80)
    origin_port = str(origin_port)
    origin = origin_site if origin_port == "80" else \
                    "{}:{}".format(origin_site, origin_port)
    # sanitize it to have a http://blah.blah.domain:XXXX form

    # DESTINATION:
    if destination_port is None:
        sys.stderr.write("destination port was not set, using 80 ...\n")
        sys.stderr.flush()
        destination_port = "80"
    # define destination as site_url:port or site_url (when 80)
    destination = destination_site if destination_port == "80" else \
                    "{}:{}".format(destination_site, destination_port)
    # sanitize it to have a http://blah.blah.domain:XXXX form

    # # use something like that to validate URLs ...
    # pieces = urlparse.urlparse(url)
    # assert all([pieces.scheme, pieces.netloc])
    # assert set(pieces.netloc) <= set(string.letters + string.digits + '-.')  # and others?
    # assert pieces.scheme in ['http', 'https', 'ftp']  # etc.

    # backup the sqlite3 database:
    # a better way to do a backup ...
    # https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup
    data_dir = get_data_dir(hg_name)
    db_location = op.join(data_dir, _SQLITEDB)
    # DB backup ready for migration with modified URLs:
    db_backup = op.join(data_dir, "{}.backup".format(_SQLITEDB))

    # there is a nice built-ion backup function in Python >=3.7:
    # this is just stupid mock code - cause i don't know
    # how get around Python version issue nicely ...
    _python_version = 3.6
    if _python_version >= 3.7:
        # nice way ...
        con = sqlite3.connect(db_location)
        bck = sqlite3.connect(db_backup)
        # context manager "with" is used here to commit
        # changes automatically if there were to exeptions
        # it does not close the connection.
        with bck:
            con.backup(bck)
        # close for now ...
        bck.close()
        con.close()
    else:
        # OMG - this is ugly ...
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
        # we could use sqlitebck module ...
        # or just stop the higlass instance and copy
        # freaking file ...
        # WE DON'T NEED TO STOP THE CONTAINER, DO WE?
        # NOT, WHEN WE DO PROPER sqlite BACKUP ...
        import shutil
        # now stop the container
        sys.stderr.write(
            "Stopping running higlass-container {} ...\n".format(hg_name)
            )
        sys.stderr.flush()
        _stop(hg_name)
        # hopefully db_location is not in use now ...
        shutil.copyfile(db_location, db_backup)


    # alright !
    # DB is backedup, - time to modify it:



    # once db_backup is done, we can connect to the DB
    # UPDATE table SET field = replace( field, 'C:\afolder\', 'C:\anewfolder\' ) WHERE field LIKE 'C:\afolder\%';
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
