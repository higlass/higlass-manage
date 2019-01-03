#!/usr/bin/env bash
set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { echo travis_fold':'end:$1; }
die() { set +v; echo "$*" 1>&2 ; sleep 1; exit 1; }
# Race condition truncates logs on Travis: "sleep" might help.
# https://github.com/travis-ci/travis-ci/issues/6018


start get-data
    ./get_test_data.sh
end get-data


start ingest
    [ -e test-hg-data ] && rm -rf test-hg-data
    [ -e test-hg-media ] && rm -rf test-hg-media

    # directories that will store data and media
    mkdir test-hg-data
    mkdir test-hg-media

    cp data/Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool \
       test-hg-media/dixon.mcool

    ./higlass_manage.py view test-hg-media/dixon.mcool

    PORT=8123
    ./higlass_manage.py start --version v0.5.0-rc.6 --port $PORT \
                                   --hg-name test-hg \
                                   --data-dir $(pwd)/test-hg-data \
                                   --media-dir $(pwd)/test-hg-media
    ./higlass_manage.py ingest --hg-name test-hg \
                                    --no-upload /media/dixon.mcool \
                                    --uid a
    docker exec higlass-manage-container-default bash -c 'grep -v "showTooltip" higlass-app/static/js/main*.chunk.js | grep function' || die 
end ingest

# check to make sure that the default options were loaded
start default-options
    ./higlass_manage.py start --version v0.5.0-rc.6 --default-track-options data/default_options.json
    docker exec higlass-manage-container-default bash -c 'grep "showTooltip" higlass-app/static/js/main*.chunk.js' || die 
end default-options

start wait
    URL="localhost:$PORT/api/v1/tilesets/"
    until curl $URL; do
        sleep 1
    done
    curl $URL | grep dixon.mcool \
        || die
end wait


start cleanup
    ./higlass_manage.py stop test-hg
end cleanup

echo 'Passed all tests'
