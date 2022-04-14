c1541 -format example,ds d64 disk.d64

find fluxvis -name \*.py | while read l; do c1541 -attach disk.d64 -write "$l" "`echo ${l##*/} | tr A-Z a-z`"; done

~/src/fluxengine/fluxengine write commodore1541 --no-verify -d disk.scp -i disk.d64
~/src/fluxengine/fluxengine read commodore1541 -s disk.scp -o disk.d64 --decoder.write_csv_to disk.csv -c 0-68x2
python3 -mfluxvis disk.scp etc/disk.jpg --oversample 3 --resolution 640 --stride 2 --tracks 35 --diameter 108
python3 -mfluxvis disk.scp etc/diskcolor.jpg --oversample 3 --resolution 640 --stride 2 --tracks 35 --diameter 108 --location disk.csv
