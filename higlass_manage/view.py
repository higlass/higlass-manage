import click
import json
import ntpath
import os
import os.path as op
import requests
import sys
import webbrowser

from higlass_manage.common import fill_filetype_and_datatype
from higlass_manage.common import get_port
from higlass_manage.common import get_data_dir
from higlass_manage.common import get_temp_dir
from higlass_manage.common import md5
from higlass_manage.common import datatype_to_tracktype
from higlass_manage.start import _start
from higlass_manage.ingest import _ingest

@click.command()
@click.argument('filename', nargs=1)
@click.option('-n', '--hg-name',
        default='default',
        help='The name for this higlass instance',
        type=str)
@click.option('--filetype', default=None, help="The type of file to ingest (e.g. cooler)")
@click.option('--datatype', default=None, help="The data type of in the input file (e.g. matrix)")
@click.option('--tracktype', default=None, help="The track type used to view this file")
@click.option('--position', default=None, help="The position in the view to place this track")
@click.option('--public-data/--no-public-data',
        default=True,
        help='Include or exclude public data in the list of available tilesets')
@click.option('--assembly', default=None, help="The assembly that this data is mapped to")
@click.option('--chromsizes-filename', default=None, help="A set of chromosome sizes to use for bed and bedpe files")
def view(filename, hg_name, filetype, datatype, tracktype, position, public_data, 
        assembly, chromsizes_filename):
    '''
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
    '''
    try:
        temp_dir = get_temp_dir(hg_name)
        print("temp_dir:", temp_dir)
    except Exception:
        _start(hg_name=hg_name)

    # check if we have a running instance
    # if not, start one

    # get a list of the available tilesets
    # check if any match the filename of this file
    # if the filenames match, check if the checksums match
    port = get_port(hg_name)
    uuid = None

    # guess filetype and datatype if they're None
    (filetype, inferred_datatype) = fill_filetype_and_datatype(filename, filetype, datatype)

    if filetype is None or inferred_datatype is None:
        print("Couldn't infer filetype or datatype ({}, {}),".format(filetype, inferred_datatype),
              "please specify them using the command line options", file=sys.stderr)
        return

    try:
        MAX_TILESETS=100000
        req = requests.get('http://localhost:{}/api/v1/tilesets/?limit={}'.format(port, MAX_TILESETS), timeout=10)
        
        tilesets = json.loads(req.content)

        for tileset in tilesets['results']:
            import_filename = op.splitext(ntpath.basename(filename))[0]
            tileset_filename = ntpath.basename(tileset['datafile'])

            subpath_index = tileset['datafile'].find('/tilesets/')
            subpath = tileset['datafile'][subpath_index + len('/tilesets/'):]

            data_dir = get_data_dir(hg_name)
            tileset_path = op.join(data_dir, subpath)

            # print("import_filename", import_filename)
            # print("tileset_filename", tileset_filename)

            if tileset_filename.find(import_filename) >= 0:
                # same filenames, make sure they're actually the same file
                # by comparing checksums
                checksum1 = md5(tileset_path)
                checksum2 = md5(filename)

                if checksum1 == checksum2:
                    uuid = tileset['uuid']
                    break
    except requests.exceptions.ConnectionError:
        print("Error getting a list of existing tilesets", file=sys.stderr)
        return

    if uuid is None:
        # we haven't found a matching tileset so we need to ingest this one
        uuid = _ingest(filename, hg_name, filetype, datatype, assembly=assembly,
                chromsizes_filename=chromsizes_filename)

    if uuid is None:
        # couldn't ingest the file
        return

    import higlass.client as hgc

    if datatype is None:
        datatype = inferred_datatype

    if tracktype is None and position is None:
        (tracktype, position) = datatype_to_tracktype(datatype)
        
        if tracktype is None:
            print("ERROR: Unknown track type for the given datatype:", datatype)
            return

    conf = hgc.ViewConf()
    view = conf.add_view()

    track = view.add_track(track_type=tracktype,
            server='http://localhost:{}/api/v1/'.format(port),
            tileset_uuid=uuid, position=position, 
            height=200)

    conf = json.loads(json.dumps(conf.to_dict()))

    conf['trackSourceServers'] = []
    conf['trackSourceServers'] += ['http://localhost:{}/api/v1/'.format(port)]

    if public_data:
        conf['trackSourceServers'] += ['http://higlass.io/api/v1/']

    # uplaod the viewconf
    res = requests.post('http://localhost:{}/api/v1/viewconfs/'.format(port),
            json={'viewconf': conf})

    if res.status_code != 200:
        print("Error posting viewconf:", res.status, res.content)
        return

    uid = json.loads(res.content)['uid']

    # make sure this test passes on Travis CI and doesn't try to open
    # a terminal-based browser which doesn't return
    if not os.environ.get('HAS_JOSH_K_SEAL_OF_APPROVAL'):
        webbrowser.open('http://localhost:{port}/app/?config={uid}'.format(
            port=port, uid=uid))
