c1541 -format example,ds d64 disk.d64

find fluxvis -name \*.py | while read l; do c1541 -attach disk.d64 -write "$l" "`echo ${l##*/} | tr A-Z a-z`"; done

~/src/fluxengine/fluxengine write commodore1541 --no-verify -d disk.scp -i disk.d64
python3 -mfluxvis disk.scp etc/disk.jpg --oversample 3 --resolution 640 --stride 2 --tracks 35 --diameter 108
