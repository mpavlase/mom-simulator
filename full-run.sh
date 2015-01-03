#!/bin/sh

function run_tests {
    rm -rf mom/exports/scenario-*
    ./scn.sh 1 1
    ./scn.sh 2 1
    ./scn.sh 3
    ./scn.sh 4
}

function batch {
    git co $1
    echo " === Using $1 as $2 ==="
    run_tests
    pushd /home/mpavlase/Documents/dp/obrazky
    cp -r _exports/* $2
    popd
}

batch fake-driver old
batch rules-1-const-guests new1
batch rules-2-big-host new2
