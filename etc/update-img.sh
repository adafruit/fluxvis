c1541 -format example,ds d64 disk.d64

for i in `seq 4`; do
for l in LICENSES/* fluxvis/*.py; do c1541 -attach disk.d64 -write $l $i`echo ${l##*/} | tr A-Z a-z`; done
i=$((i+1))
done

~/src/fluxengine/fluxengine write commodore1541 --no-verify -d disk.scp -i disk.d64
PYTHONPATH=../greaseweazle/scripts/ python3 -mfluxvis disk.scp etc/disk.jpg --stride 2 --tracks 35 --oversample 3 --resolution 640
