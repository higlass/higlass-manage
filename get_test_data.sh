#!/usr/bin/env bash
set -e

if [! -d data]; then
    mkdir data
fi;

FILES=$(cat <<END
Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool
END
)

for FILE in $FILES; do
  [ -e data/$FILE ] || wget -P data/ https://s3.amazonaws.com/pkerp/public/$FILE
done

