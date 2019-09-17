import docker
import hashlib
import os
import os.path as op
import slugid
import sys

CONTAINER_PREFIX = 'higlass-manage-container'
NETWORK_PREFIX = 'higlass-manage-network'
REDIS_PREFIX = 'higlass-manage-redis'
REDIS_CONF = '/usr/local/etc/redis/redis.conf'

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def hg_name_to_container_name(hg_name):
    return '{}-{}'.format(CONTAINER_PREFIX, hg_name)

def hg_name_to_network_name(hg_name):
    return '{}-{}'.format(NETWORK_PREFIX, hg_name)

def hg_name_to_redis_name(hg_name):
    return '{}-{}'.format(REDIS_PREFIX, hg_name)

def get_port(hg_name):
    client = docker.from_env()

    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)
    port = config['HostConfig']['PortBindings']['80/tcp'][0]['HostPort']

    return port

def fill_filetype_and_datatype(filename, filetype, datatype):
    '''
    If no filetype or datatype are provided, add them
    based on the given filename.

    Parameters:
    ----------
    filename: str
        The name of the file
    filetype: str
        The type of the file (can be None)
    datatype: str
        The datatype for the data in the file (can be None)

    Returns:
    --------
    (filetype, datatype): (str, str)
        Filled in filetype and datatype based on the given filename
    '''
    if filetype is None:
        # no filetype provided, try a few common filetypes
        filetype = infer_filetype(filename)
        print('Inferred filetype:', filetype)

        if filetype is None:
            recommended_filetype = recommend_filetype(filename)

            print('Unknown filetype, please specify using the --filetype option', file=sys.stderr)
            if recommended_filetype is not None:
                print("Based on the filename, you may want to try the filetype: {}".format(recommended_filetype))

            return (None, None)

    if datatype is None:
        datatype = infer_datatype(filetype)
        print('Inferred datatype:', datatype)

        if datatype is None:
            recommended_datatype = recommend_datatype(filetype)
            print('Unknown datatype, please specify using the --datatype option', file=sys.stderr)
            if recommended_datatype is not None:
                print("Based on the filetype, you may want to try the datatype: {}".format(recommended_datatype))

    return (filetype, datatype)

def recommend_filetype(filename):
    if op.splitext(filename)[1] == '.bed':
        return 'bedfile'
    if op.splitext(filename)[1] == '.bedpe':
        return 'bedpe'

def recommend_datatype(filetype):
    if filetype == 'bedfile':
        return 'bedlike'

def datatype_to_tracktype(datatype):
    if datatype == 'matrix':
        return ('heatmap', 'center')
    elif datatype == 'vector':
        return ('horizontal-bar', 'top')
    elif datatype == 'gene-annotations':
        return ('horizontal-gene-annotations', 'top')
    elif datatype == 'chromsizes':
        return ('horizontal-chromosome-labels', 'top')
    elif datatype == '2d-rectangle-domains':
        return ('2d-rectangle-domains', 'center')
    elif datatype == 'bedlike':
        return ('bedlike', 'top')
    elif datatype == 'reads':
        return ('pileup', 'top')

    return (None, None)

def infer_filetype(filename):
    _,ext = op.splitext(filename)

    if ext.lower() == '.bw' or ext.lower() == '.bigwig':
        return 'bigwig'
    elif ext.lower() == '.mcool' or ext.lower() == '.cool':
        return 'cooler'
    elif ext.lower() == '.htime':
        return 'time-interval-json'
    elif ext.lower() == '.hitile':
        return 'hitile'
    elif ext.lower() == '.beddb':
        return 'beddb'
    elif ext.lower() == '.bam':
        return 'bam'

    return None

def infer_datatype(filetype):
    if filetype == 'cooler':
        return 'matrix'
    if filetype == 'bigwig':
        return 'vector'
    if filetype == 'time-interval-json':
        return 'time-interval'
    if filetype == 'hitile':
        return 'vector'
    if filetype == 'beddb':
        return 'bedlike'
    if filetype == 'bam':
        return 'reads'

def import_file(hg_name, filepath, filetype, datatype, assembly, name, uid, no_upload, project_name):
    # get this container's temporary directory
    if not no_upload or filetype == 'bam':
        temp_dir = get_temp_dir(hg_name)
        if not op.exists(temp_dir):
            os.makedirs(temp_dir)

        filename = op.split(filepath)[1]
        to_import_path = op.join(temp_dir, filename)

        if to_import_path != filepath:
            # if this file already exists in the temporary dir
            # remove it
            if op.exists(to_import_path):
                print("Removing existing file in temporary dir:", to_import_path)
                os.remove(to_import_path)

            os.link(filepath, to_import_path)
    else:
        filename = filepath

    coordSystem = '--coordSystem {}'.format(assembly) if assembly is not None else ''
    name_text = '--name "{}"'.format(name) if name is not None else ''
    project_name_text = '--project-name "{}"'.format(project_name) if project_name is not None else ''

    print('name_text: {}'.format(name_text))

    client = docker.from_env()
    print("hg_name:", hg_name)
    container_name = hg_name_to_container_name(hg_name)
    container = client.containers.get(container_name)

    uid = uid if uid is not None else slugid.nice()

    print("filetype", filetype)
    if filetype == 'bam':
        ## bamfiles require special treatment because they will be placed in
        # the static directory
        index_filepath = filepath + '.bai'
        if not op.exists(index_filepath):
            print(f"Index file not found at {index_filepath}")
            sys.exit(1)

        data_dir = get_data_dir(hg_name)
        static_dir = op.join(data_dir, 'static')


        static_filename = op.join(static_dir, filename)
        static_index = op.join(static_dir, filename + ".bai")

        if op.exists(static_filename) or op.exists(static_index):
            print("generating uuid")
            uuid = slugid.nice()
            static_filename = f'{op.splitext(static_filename)[0]}.{uuid}.bam'
            static_index = f'{op.splitext(op.splitext(static_index)[0])[0]}.{uuid}.bam.bai'

        os.symlink(filepath, static_filename)
        os.symlink(filepath, static_index)

        datafile = op.join('static', op.split(static_filename)[1])

        command = (
            'python higlass-server/manage.py shell --command="' +
            'import tilesets.models as tm; ' +
            'tm.Tileset.objects.create('
                f"""datafile='{static_filename}',""" +
                f"""filetype='{filetype}',""" +
                f"""datatype='{datatype}',""" +
                f"""coordSystem='{coordSystem}',""" +
                f"""coordSystem2='{coordSystem}',""" +
                f"""owner=None,""" +
                f"""project={project_name},""" +
                f"""uuid='{uid}',""" +
                f"""temporary=False,""" +
                f"""name='{name}')""" +
            ';"')
        print("command:", command)
    elif no_upload:
        command =  ('python higlass-server/manage.py ingest_tileset --filename' +
                ' {}'.format(filename.replace(' ', '\ ')) +
                ' --uid {} --filetype {} --datatype {} {} {} {} --no-upload'.format(
                    uid, filetype, datatype, name_text, project_name_text, coordSystem)
                )
    else:
        command =  ('python higlass-server/manage.py ingest_tileset --filename' +
                ' /tmp/{}'.format(filename.replace(' ', '\ ')) +
                ' --uid {} --filetype {} --datatype {} {} {} {}'.format(
                    uid, filetype, datatype, name_text, project_name_text, coordSystem))

    (exit_code, output) = container.exec_run(command)

    if exit_code != 0:
        print("ERROR:", output.decode('utf8'), file=sys.stderr)
        return None

    return uid

def get_temp_dir(hg_name):
    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)

    print('state', config['State']['Running'])

    if config['State']['Running'] != True:
        raise HiGlassNotRunningException()

    for mount in config['Mounts']:
        if mount['Destination'] == '/tmp':
            return mount['Source']

def get_data_dir(hg_name):
    client = docker.from_env()
    container_name = hg_name_to_container_name(hg_name)
    config = client.api.inspect_container(container_name)

    for mount in config['Mounts']:
        if mount['Destination'] == '/data':
            return mount['Source']

class HiGlassNotRunningException(Exception):
    pass
