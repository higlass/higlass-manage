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
    ./higlass_manage.py start --port $PORT \
                                   --hg-name test-hg \
                                   --data-dir $(pwd)/test-hg-data \
                                   --media-dir $(pwd)/test-hg-media
    ./higlass_manage.py ingest --hg-name test-hg \
                                    --no-upload /media/dixon.mcool \
                                    --uid a
end ingest


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
