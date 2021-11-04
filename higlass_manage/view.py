import click

from contextlib import closing

import json
import ntpath
import os
import os.path as op
import requests
import socket
import sys
import webbrowser


from higlass_manage.common import CONTAINER_PREFIX
from higlass_manage.common import fill_filetype_and_datatype
from higlass_manage.common import get_port
from higlass_manage.common import get_data_dir
from higlass_manage.common import get_temp_dir
from higlass_manage.common import md5
from higlass_manage.common import datatype_to_tracktype
from higlass_manage.common import tileset_uuid_by_exact_filepath
from higlass_manage.common import tileset_uuid_by_filename

from higlass_manage.start import _start
from higlass_manage.ingest import _ingest


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@click.command()
@click.argument("filename", nargs=1)
@click.option(
    "--filetype", default=None, help="The type of file to ingest (e.g. cooler)"
)
@click.option(
    "--datatype", default=None, help="The data type of in the input file (e.g. matrix)"
)
@click.option("--tracktype", default=None, help="The track type used to view this file")
@click.option(
    "--position", default=None, help="The position in the view to place this track"
)
@click.option(
    "--public-data/--no-public-data",
    default=True,
    help="Include or exclude public data in the list of available tilesets",
)
@click.option(
    "--assembly", default=None, help="The assembly that this data is mapped to"
)
@click.option(
    "--chromsizes-filename",
    default=None,
    help="A set of chromosome sizes to use for bed and bedpe files",
)
def view(
    filename,
    filetype,
    datatype,
    tracktype,
    position,
    public_data,
    assembly,
    chromsizes_filename,
):
    """
    View a file in higlass.

    The user can specify an instance to view it in. If one is
    not specified the default will be used. If the default isn't
    running, it will be started.

    Parameters:
    -----------
    hg_name: string
        The name of the higlass instance
    filename: string
        The name of the file to view
    """
    port = find_free_port()
    hg_name = "viewer"

    try:
        get_temp_dir(hg_name)
    except Exception:
        _start(hg_name=hg_name, media_dir="/", port=port)

    # check if we have a running instance
    # if not, start one

    # get a list of the available tilesets
    # check if any match the filename of this file
    # if the filenames match, check if the checksums match
    port = get_port(hg_name)
    uuid = None

    # guess filetype and datatype if they're None
    (filetype, inferred_datatype) = fill_filetype_and_datatype(
        filename, filetype, datatype
    )

    if filetype is None or inferred_datatype is None:
        print(
            "Couldn't infer filetype or datatype ({}, {}),".format(
                filetype, inferred_datatype
            ),
            "please specify them using the command line options",
            file=sys.stderr,
        )
        return

    url = False
    if filename[:7] == "http://" or filename[:8] == "https://":
        url = True

    if url and filetype != "bam":
        print("Only bam files can be specified as urls", tile=sys.stderr)
        return

    # always ingest since we're just linking the file
    # don't need to keep track of whether it's in the DB

    uuid = _ingest(
        op.join("/media", op.relpath(op.abspath(filename), "/")),
        hg_name,
        filetype,
        datatype,
        assembly=assembly,
        chromsizes_filename=chromsizes_filename,
        url=url,
        no_upload=True,
    )

    if uuid is None:
        # couldn't ingest the file
        return

    from higlass.client import Track, View, ViewConf

    if datatype is None:
        datatype = inferred_datatype

    if tracktype is None and position is None:
        (tracktype, position) = datatype_to_tracktype(datatype)

        if tracktype is None:
            print("ERROR: Unknown track type for the given datatype:", datatype)
            return

    view = View(
        [
            Track(
                track_type=tracktype,
                position=position,
                tileset_uuid=uuid,
                server="http://localhost:{}/api/v1/".format(port),
                height=200,
            )
        ]
    )

    viewconf = ViewConf([view])

    conf = viewconf.to_dict()

    if filetype == "bam" and url:
        track = conf["views"][0]["tracks"]["top"][0]
        del track["tilesetUid"]
        del track["server"]
        track["data"] = {"type": "bam", "url": filename}

        conf["views"][0]["tracks"]["top"].insert(0, {"type": "top-axis"})
        # create a smaller viewport so that people can see their reads
        conf["views"][0]["initialXDomain"] = [0, 40000]

    conf["trackSourceServers"] = []
    conf["trackSourceServers"] += ["http://localhost:{}/api/v1/".format(port)]

    if public_data:
        conf["trackSourceServers"] += ["http://higlass.io/api/v1/"]

    # uplaod the viewconf
    res = requests.post(
        "http://localhost:{}/api/v1/viewconfs/".format(port), json={"viewconf": conf}
    )

    if res.status_code != 200:
        print("Error posting viewconf:", res.status, res.content)
        return

    uid = json.loads(res.content)["uid"]

    # make sure this test passes on Travis CI and doesn't try to open
    # a terminal-based browser which doesn't return
    if not os.environ.get("HAS_JOSH_K_SEAL_OF_APPROVAL"):
        webbrowser.open(
            "http://localhost:{port}/app/?config={uid}".format(port=port, uid=uid)
        )
