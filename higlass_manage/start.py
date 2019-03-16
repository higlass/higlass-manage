import click
import docker
import json
import os
import os.path as op
import requests
import slugid
import sys
import time

from higlass_manage.common import CONTAINER_PREFIX

@click.command()
@click.option('-t', '--temp-dir',
        default='/tmp/higlass-docker',
        help='The temp directory to use',
        type=str)
@click.option('-d', '--data-dir',
        default='~/hg-data',
        help='The higlass data directory to use',
        type=str)
@click.option('-v', '--version',
        default='latest',
        help='The version of the Docker container to use',
        type=str)
@click.option('-p', '--port',
        default=8989,
        help='The port that the HiGlass instance should run on',
        type=str)
@click.option('-n', '--hg-name',
        default='default',
        help='The name for this higlass instance',
        type=str)
@click.option('-s', '--site-url',
        default=None,
        help='When creating an external-facing instance, enter its IP or hostname using this parameter',
        type=str)
@click.option('-m', '--media-dir',
        default=None,
        help='Use a specific media directory for uploaded files',
        type=str)
@click.option('--public-data/--no-public-data',
        default=True,
        help='Include or exclude public data in the list of available tilesets')
@click.option('--default-track-options',
        default=None,
        help="Specify a json file containing default track options")
def start(temp_dir,
            data_dir,
            version,
            port,
            hg_name,
            site_url,
            media_dir,
            public_data,
            default_track_options):
    _start(temp_dir,
            data_dir,
            version,
            port,
            hg_name,
            site_url,
            media_dir,
            public_data,
            default_track_options)

def _start(temp_dir='/tmp/higlass-docker', 
        data_dir='~/hg-data', 
        version='latest', 
        port=8989, 
        hg_name='default', 
        site_url=None,
        media_dir=None, 
        public_data=True,
        default_track_options=None):
    '''
    Start a HiGlass instance
    '''
    container_name = '{}-{}'.format(CONTAINER_PREFIX,hg_name)

    client = docker.from_env()

    try:
        container = client.containers.get(container_name)

        print('Stopping previously running container')
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        # container isn't running so no need to stop it
        pass
    except requests.exceptions.ConnectionError:
        print('Error connecting to the Docker daemon, make sure it is started and you are logged in.')
        return


    if version == 'local':
        image = client.images.get('image-default')
    else:
        sys.stdout.write("Pulling latest image... ")
        sys.stdout.flush()
        image = client.images.pull('higlass/higlass-docker', version)
        sys.stdout.write("done")
        sys.stdout.flush()

    data_dir = op.expanduser(data_dir)
    temp_dir = op.expanduser(temp_dir)

    if not op.exists(temp_dir):
        os.makedirs(temp_dir)
    if not op.exists(data_dir):
        os.makedirs(data_dir)

    environment = {}

    if site_url is not None:
        environment['SITE_URL'] = site_url

    print('Data directory:', data_dir)
    print('Temp directory:', temp_dir)

    version_addition = '' if version is None else ':{}'.format(version)

    print('Starting...', hg_name, port)
    volumes={
        temp_dir : { 'bind' : '/tmp', 'mode' : 'rw' },
        data_dir : { 'bind' : '/data', 'mode' : 'rw' }
        }

    if media_dir:
        volumes[media_dir] = { 'bind' : '/media', 'mode' : 'rw' }
        environment['HIGLASS_MEDIA_ROOT'] = '/media'


    container = client.containers.run(image,
            ports={80 : port},
            volumes=volumes,
            name=container_name,
            environment=environment,
            detach=True)
    print('Docker started: {}'.format(container_name))

    started = False
    counter = 1
    while not started:
        try:
            print("sending request", counter)
            counter += 1
            req = requests.get('http://localhost:{}/api/v1/viewconfs/?d=default'.format(port), 
                    timeout=5)
            # print("request returned", req.status_code, req.content)

            if req.status_code != 200:
                print("Non 200 status code returned ({}), waiting...".format(req.status_code))
                time.sleep(0.5)
            else:
                started = True
        except requests.exceptions.ConnectionError:
            print("Waiting to start (tilesets)...")
            time.sleep(0.5)
        except requests.exceptions.ReadTimout:
            print("Request timed out")
            time.sleep(0.5)

    print("public_data:", public_data)

    if not public_data or default_track_options is not None:
        # we're going to be changing the higlass js file so first we copy it to a location
        # with a new hash
        new_hash = slugid.nice()

        sed_command = """bash -c 'cp higlass-app/static/js/main.*.chunk.js higlass-app/static/js/main.{}.chunk.js'""".format(new_hash)

        ret = container.exec_run(sed_command)   
             
    if not public_data:
        config = json.loads(req.content.decode('utf-8'))
        config['trackSourceServers'] = ['/api/v1']
        started = True
        # print('config', json.dumps(config, indent=2))
        config = {
                'uid': 'default_local',
                'viewconf': config
                }

        ret = container.exec_run("""python higlass-server/manage.py shell --command="import tilesets.models as tm; o = tm.ViewConf.objects.get(uuid='default_local'); o.delete();" """);
        ret = requests.post('http://localhost:{}/api/v1/viewconfs/'.format(port), json=config)
        print('ret:', ret.content)
        # ret = container.exec_run('echo "import tilesets.models as tm; tm.ViewConf.get(uuid={}default{}).delete()" | python higlass-server/manage.py shell'.format("'", "'"), tty=True)
        ret = container.exec_run("""bash -c 'sed -i '"'"'s/"default"/"default_local"/g'"'"' higlass-app/static/js/main.*.chunk.js'""".format(new_hash))
        print('ret:', ret)

    if default_track_options is not None:
        with open(default_track_options, 'r') as f:
            default_options_json = json.load(f)

            sed_command = """bash -c 'sed -i '"'"'s/assign({{}},this.props.options/assign({{defaultOptions: {} }},this.props.options/g'"'"' """.format(json.dumps(default_options_json))
            sed_command += " higlass-app/static/js/main.*.chunk.js'"
            # print("sed_command:", sed_command)

            ret = container.exec_run(sed_command)

    # print("ret:", ret)

    sed_command = """bash -c 'sed -i '"'"'s/main.*.chunk.js/main.invalid.chunk.js/g'"'"' """
    sed_command += " higlass-app/precache-manifest.*.js'"

    ret = container.exec_run(sed_command)
    # print("ret:", ret)

    sed_command = """bash -c 'sed -i '"'"'s/index.html/index_invalidated_by_higlass_manage/g'"'"' """
    sed_command += " higlass-app/precache-manifest.*.js'"

    ret = container.exec_run(sed_command)
    # print("ret:", ret)
    print("Replaced js file")


    print("Started")
