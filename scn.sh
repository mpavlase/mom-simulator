#!/bin/sh
# This script automate usage mom simulator to get bunch of results.

# P as prefix
P=mom

I=$1
shift

mkdir -p $P/exports

LOG=mom.log

# step 1 - prepare data for simulator to know location
cp $P/scenario.${I}.csv $P/scenario.csv
echo "Run scenario number $I"

# step 2 - run MoM
echo "MoM simulator is in progress..."
time ./momd -c mom.fake.conf 2> $P/$LOG

echo "Backup all data to own separate folder"

cd $P
OUT="exports/scenario-$I"
rm -rf $OUT
mkdir -p $OUT
cp plot.json $OUT
cp scenario.csv $OUT
cp $LOG $OUT

echo -n "Export output as PNG... "
./show_plot.py -q -f plot.json -w 2 -o $OUT/plot_${I}.png
echo -n "EPS... "
./show_plot.py -q -f plot.json -w 2 -o $OUT/plot_${I}.eps
./show_plot.py -f plot.json -w 2
echo "Done."
