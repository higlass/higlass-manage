#!/usr/bin/env bash
set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { echo travis_fold':'end:$1; }
die() { set +v; echo "$*" 1>&2 ; sleep 1; exit 1; }
# Race condition truncates logs on Travis: "sleep" might help.
# https://github.com/travis-ci/travis-ci/issues/6018

# Due to Travis CI permissions, create temporary work
# directory that is relative to the home directory
TMPDIR=$(mktemp --directory --tmpdir=${HOME})

# Make sure it gets removed even if the script exits abnormally
#trap "exit 1"           HUP INT PIPE QUIT TERM
#trap 'rm -rf "$TMPDIR"' EXIT

start get-data
    ./get_test_data.sh
end get-data

HIGLASS_DOCKER_VERSION=v0.6.9;

start ingest
    [ -e ${TMPDIR}/test-hg-data ] && rm -rf ${TMPDIR}/test-hg-data
    [ -e ${TMPDIR}/test-hg-media ] && rm -rf ${TMPDIR}/test-hg-media

    # ingest a bedfile; useful for testing the aggregate
    # function that gets called first
    higlass-manage ingest --filetype bedfile \
        --datatype bedlike --assembly hg19\
        data/ctcf_known1_100.bed

    # directories that will store data and media
    mkdir ${TMPDIR}/test-hg-data
    mkdir ${TMPDIR}/test-hg-media

    cp data/Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool \
       ${TMPDIR}/test-hg-media/dixon.mcool

    higlass-manage view ${TMPDIR}/test-hg-media/dixon.mcool

    PORT=8123
    higlass-manage start --version ${HIGLASS_DOCKER_VERSION} --port ${PORT} \
                                   --hg-name test-hg \
                                   --data-dir ${TMPDIR}/test-hg-data \
                                   --media-dir ${TMPDIR}/test-hg-media
    higlass-manage ingest --hg-name test-hg \
                                    --no-upload /media/dixon.mcool \
                                    --uid a
    docker exec higlass-manage-container-default bash -c 'grep -v "showTooltip" higlass-app/static/js/main*.chunk.js | grep function' || die 
end ingest

# check to make sure that the default options were loaded
start default-options
    higlass-manage start --version ${HIGLASS_DOCKER_VERSION} --default-track-options data/default_options.json
    docker exec higlass-manage-container-default bash -c 'grep "showTooltip" higlass-app/static/js/main*.chunk.js' || die 
end default-options

start wait
    URL="localhost:$PORT/api/v1/tilesets/"
    until curl ${URL}; do
        sleep 1
    done
    curl ${URL} | grep dixon.mcool \
        || die
end wait

start cleanup
    higlass-manage stop test-hg
end cleanup

start redis
    mkdir ${TMPDIR}/test-hg-data-with-redis
    mkdir ${TMPDIR}/test-hg-media-with-redis
    mkdir ${TMPDIR}/test-redis

    PORT=8124
    higlass-manage start --version $HIGLASS_DOCKER_VERSION \
		   --port ${PORT} \
		   --hg-name test-hg-with-redis \
		   --data-dir ${TMPDIR}/test-hg-data-with-redis \
		   --media-dir ${TMPDIR}/test-hg-media-with-redis \
		   --redis-dir ${TMPDIR}/test-redis \
		   --use-redis

    docker exec -i higlass-manage-redis-test-hg-with-redis 'redis-cli' < <(echo ping) || die
end redis

start cleanup
    higlass-manage stop test-hg-with-redis
end cleanup

echo 'Passed all tests'
