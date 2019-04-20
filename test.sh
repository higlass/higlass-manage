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

HIGLASS_DOCKER_VERSION=v0.6.9;


start ingest
    [ -e test-hg-data ] && rm -rf test-hg-data
    [ -e test-hg-media ] && rm -rf test-hg-media

    # ingest a bedfile; useful for testing the aggregate
    # function that gets called first
    higlass-manage ingest --filetype bedfile \
        --datatype bedlike --assembly hg19\
        data/ctcf_known1_100.bed

    # directories that will store data and media
    mkdir test-hg-data
    mkdir test-hg-media

    cp data/Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool \
       test-hg-media/dixon.mcool

    higlass-manage view test-hg-media/dixon.mcool

    PORT=8123
    higlass-manage start --version $HIGLASS_DOCKER_VERSION --port $PORT \
                                   --hg-name test-hg \
                                   --data-dir $(pwd)/test-hg-data \
                                   --media-dir $(pwd)/test-hg-media
    higlass-manage ingest --hg-name test-hg \
                                    --no-upload /media/dixon.mcool \
                                    --uid a
    docker exec higlass-manage-container-default bash -c 'grep -v "showTooltip" higlass-app/static/js/main*.chunk.js | grep function' || die 
end ingest

# check to make sure that the default options were loaded
start default-options
    higlass-manage start --version $HIGLASS_DOCKER_VERSION --default-track-options data/default_options.json
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
    higlass-manage stop test-hg
end cleanup

start redis
    [ -e test-hg-data ] && rm -rf test-hg-data
    [ -e test-hg-media ] && rm -rf test-hg-media
    [ -e test-redis ] && rm -rf test-redis

    mkdir test-hg-data
    mkdir test-hg-media
    mkdir test-redis

    higlass-manage start --version $HIGLASS_DOCKER_VERSION \
		   --hg-name test-hg \
		   --data-dir $(pwd)/test-hg-data \
		   --media-dir $(pwd)/test-hg-media \
		   --redis-dir $(pwd)/test-redis \
		   --use-redis

    docker exec -i higlass-manage-redis-default 'redis-cli' < <(echo ping) || die
end redis

start cleanup
    higlass-manage stop test-hg
end cleanup

echo 'Passed all tests'
