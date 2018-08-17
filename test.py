#!/usr/bin/python

import os.path as op
import subprocess as sp
import time

sp.call('bash get_test_data.sh', shell=True)

if op.exists('test-hg_data'):
    sp.call('rm -rf test-hg-data', shell=True)
if op.exists('test-hg-media'):
    sp.call('rm -rf test-hg-media', shell=True)

# directories that will store data and media
sp.call('mkdir test-hg-data', shell=True)
sp.call('mkdir test-hg-media', shell=True)

sp.call('cp data/Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool test-hg-media/dixon.mcool', 
        shell=True)

sp.call('python higlass_manage.py start --port 8123 --hg-name test-hg --data-dir $(pwd)/test-hg-data --media-dir $(pwd)/test-hg-media', shell=True)
sp.call('python higlass_manage.py ingest --hg-name test-hg --no-upload dixon.mcool --uid a', shell=True)

# first one will return bad gateway
out = sp.check_output('curl localhost:8123/api/v1/tilesets', shell=True).decode('utf8')
while out.find('Bad Gateway') >= 0:
    time.sleep(1)
    out = sp.check_output('curl localhost:8123/api/v1/tilesets/', shell=True).decode('utf8')
    print('out:', out)

# make sure our file was successfully added
assert(out.find('dixon.mcool') >= 0)
sp.call('python higlass_manage.py stop test-hg', shell=True)

sp.call('rm -rf test-hg-data', shell=True)
sp.call('rm -rf test-hg-media', shell=True)

print("Passed all tests")
