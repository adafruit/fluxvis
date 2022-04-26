#!/bin/sh
set -e
c1541 -format example,ds d64 disk.d64

find fluxvis -name \*.py | while read l; do
    fn=$(echo $l | sha256sum | cut -b -16)
    c1541 -attach disk.d64 -write "$l" "$fn"
done

~/src/fluxengine/fluxengine write commodore1541 --no-verify -d disk.scp -i disk.d64 --drive.rotational_period_ms 200
~/src/fluxengine/fluxengine read commodore1541 -s disk.scp -o disk.d64 --decoder.write_csv_to disk.csv --drive.rotational_period_ms 200 -c 0-34
python3 -mfluxvis --oversample 3 --resolution 640 --stride 2 --tracks 35 --diameter 108                        write disk.scp etc/disk.jpg
python3 -mfluxvis --oversample 3 --resolution 640 --stride 2 --tracks 35 --diameter 108 --location disk.csv    write disk.scp etc/diskcolor.jpg
