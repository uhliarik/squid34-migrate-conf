#!/bin/bash
#
# This is just simple test file, feel free to modify it
#
# Lubos Uhliarik
#
TESTS_DIR="tests"
BASE_DIR=$(pwd)
RESULT_DIR="results"

# delete old result dir
rm -rf "$RESULT_DIR"

# create result directory
cp -R "$TESTS_DIR" $RESULT_DIR

# execute all tests
for i in "$RESULT_DIR"/* ; do
    echo ">>>>> Running test $(basename $i) ..."
    cd "$i"
    python "$BASE_DIR/squid-migrate-conf.py" --conf "squid.conf" --write-changes
    cd -
    echo ">>>>> Finished"
done