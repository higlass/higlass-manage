import click
import os.path as op
import shutil
import sqlite3

from higlass_manage.common import get_data_dir


@click.command()
@click.argument("hg_name", nargs=-1)
@click.option(
    "--hg-name",
    default="default",
    help="The name of the higlass container to import this file to",
)
@click.option(
    "--destination-url",
    default="localhost",
    help="site-url at the destination of migration",
)
def migrate(hg_name,destination_url):
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

    data_dir = get_data_dir(hg_name)
    db_location = op.join(data_dir, "db.sqlite3")
    # create DB backup that will be prepared for migration
    # by modification of URLs:
    db_backup = op.join(data_dir, "db.sqlite3.backup")

    # We have to make sure db_location is not in use now
    # before copying.
    # What should we do - stop hg_name container if it's
    # running - or just make sure it's not running ...
    shutil.copyfile(db_location,db_backup)


    # once DB is backed up - we need to figure out SITE_URL of
    # the higlass instance we are trying to migrate
    # maybe something like that:
    hg_environment["SITE_URL"] = site_url

    # once db_backup is done, we can connect to the DB
    # UPDATE table SET field = replace( field, 'C:\afolder\', 'C:\anewfolder\' ) WHERE field LIKE 'C:\afolder\%';
    conn = None
    try:
        conn = sqlite3.connect(db_backup)
    except Error as e:
        print(e)

    sql = ''' UPDATE table
              SET field = replace( field,
                  {current_url} ,
                  {destination_url} )
                  WHERE field LIKE {current_url}
           '''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    conn.close()
