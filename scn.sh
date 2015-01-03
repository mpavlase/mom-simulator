#!/bin/sh
# This script automate usage mom simulator to get bunch of results.

# P as prefix
P=mom

I=$1
shift

WIDTH=${1:-2}
shift
#echo "I = $I width=$WIDTH"

mkdir -p $P/exports

LOG=mom.log

echo "Generate all scenarios..."
pushd $P
./scenario_generator.py
popd

# step 1 - prepare data for simulator to know location
cp $P/scenario.${I}.csv $P/scenario.csv
echo "Run scenario number $I"

# step 2 - run MoM
echo "MoM simulator is in progress..."
#time ./momd -c mom.fake.conf 2> $P/$LOG

echo "Backup all data to own separate folder"

cd $P
OUT="exports/scenario-$I"
rm -rf $OUT
mkdir -p $OUT
cp plot.json $OUT
cp scenario.csv $OUT
#cp $LOG $OUT

echo -n "Export output as PNG... "
./show_plot.py -q -f plot.json -w $WIDTH -o $OUT/plot.png
echo "EPS"
./show_plot.py -q -f plot.json -w $WIDTH -o $OUT/plot.eps
echo -n "Waiting for close plot window... "
#./show_plot.py -f plot.json -w 2
echo "Done."
