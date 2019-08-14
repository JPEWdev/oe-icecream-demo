#! /bin/bash
#
# Copyright 2019 Garmin Ltd. or its subsidiaries
#
# SPDX-License-Identifier: Apache-2.0

# exit on any error and unset variables
set -u -e -o pipefail

THIS_DIR="$(readlink -f $(dirname $0))"

if [ -z "${1:-}" ]; then
    echo "Usage: $0 [FIRST] LAST"
    exit 1
fi

for i in $(seq $@); do
    echo "Build $i"
    RESULTS_DIR=$THIS_DIR/stats/build$i
    $THIS_DIR/test_icecream.sh $RESULTS_DIR
done

