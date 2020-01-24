#!/usr/bin/env bash
set -e

mkdir -p data

FILES=$(cat <<END
Dixon2012-J1-NcoI-R1-filtered.100kb.multires.cool
ctcf_known1_100.bed
END
)

for FILE in $FILES; do
  [ -e data/$FILE ] || wget -P data/ https://s3.amazonaws.com/pkerp/public/$FILE
done


VIEWCONF=$(cat <<EOF
{
  "uid": "test-123",
  "viewconf": {
      "editable": true,
      "views": [
        {
          "uid": "myviewconf123",
          "tracks": {
            "top": [],
            "center": [
              {
                "type": "heatmap",
                "options": {
                  "valueScaleMax": 0.2
                },
                "tilesetUid": "a",
                "server": "http://localhost:8123/api/v1/",
                "height": 250
              }
            ],
            "left": [],
            "right": [],
            "bottom": []
          },
          "layout": {
            "w": 12,
            "h": 6,
            "x": 0,
            "y": 0
          }
        }
      ],
      "trackSourceServers": [
        "http://localhost:8123/api/v1/"
      ],
      "locationLocks": {
        "locksByViewUid": {},
        "locksDict": {}
      },
      "zoomLocks": {
        "locksByViewUid": {},
        "locksDict": {}
      },
      "exportViewUrl": "http://localhost:8123/api/v1/viewconfs"
    }
}
EOF
)

echo $VIEWCONF > data/test_viewconf.json