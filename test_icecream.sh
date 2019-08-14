#! /bin/bash
#
# Copyright 2019 Garmin Ltd. or its subsidiaries
#
# SPDX-License-Identifier: Apache-2.0

# exit on any error and unset variables
set -u -e -o pipefail

THIS_DIR="$(readlink -f $(dirname $0))"

RESULTS_DIR="$(readlink -m ${1:-$THIS_DIR/results})"

IMAGE="core-image-minimal"

if ! which icecc > /dev/null 2>&1; then
    echo "icecc not found. Please install and configure icecream"
    exit 1
fi

if [ ! -d $THIS_DIR/poky ]; then
    git clone -n git://git.yoctoproject.org/poky $THIS_DIR/poky
fi
git -C $THIS_DIR/poky checkout a76b6b317c9b9d8aef348f4639de8b0224d27a4d

if [ ! -d $THIS_DIR/poky/meta-pyrex ]; then
    git clone -n https://github.com/garmin/pyrex.git $THIS_DIR/poky/meta-pyrex
fi
git -C $THIS_DIR/poky/meta-pyrex checkout 7b3e0b63156a6e42fc438d2faad84a20172a9524
ln -sf ./meta-pyrex/pyrex-init-build-env $THIS_DIR/poky/pyrex-init-build-env

mkdir -p $THIS_DIR/poky/downloads

do_build() {
    local NAME="$1"
    # subshell
    (
    # Cleanup any old build output
    cd $THIS_DIR/poky
    rm -rf build-$NAME

    # Source the environment. This will change the CWD
    set +u
    export TEMPLATECONF="$THIS_DIR/conf/$NAME"
    . pyrex-init-build-env build-$NAME
    set -u

    # Unpack all source. Downloading/unpacking has the most timing variability
    # between builds, so it is done as a separate step to help eliminate noise
    # in the results
    echo "Run bitbake"
    bitbake --runonly unpack $IMAGE

    # Remove any old buildstats so that only one possible directory remains to
    # be copied later
    rm -rf tmp/buildstats

    bitbake $IMAGE
    cp -r tmp/buildstats/* $RESULTS_DIR/$NAME
    )
}

rm -rf $RESULTS_DIR || true
mkdir -p $RESULTS_DIR
do_build without-icecream
do_build with-icecream

$THIS_DIR/poky/scripts/buildstats-diff --diff-attr cputime $RESULTS_DIR/without-icecream $RESULTS_DIR/with-icecream > $RESULTS_DIR/cputime.txt
$THIS_DIR/poky/scripts/buildstats-diff --diff-attr walltime $RESULTS_DIR/without-icecream $RESULTS_DIR/with-icecream > $RESULTS_DIR/walltime.txt

TOTALS_FILE=$RESULTS_DIR/task_totals.txt
rm -f $TOTALS_FILE
for task in do_configure do_compile do_install do_package_write_rpm; do
    echo "$task:" >> $TOTALS_FILE
    $THIS_DIR/poky/scripts/buildstats-diff --only-task $task --diff-attr cputime $RESULTS_DIR/without-icecream $RESULTS_DIR/with-icecream | tail -2 >> $TOTALS_FILE
    $THIS_DIR/poky/scripts/buildstats-diff --only-task $task --diff-attr walltime $RESULTS_DIR/without-icecream $RESULTS_DIR/with-icecream | tail -2 >> $TOTALS_FILE
    echo "" >> $TOTALS_FILE
done

ELAPSED_WITHOUT_ICECREAM=$(grep '^Elapsed time:' $RESULTS_DIR/without-icecream/build_stats | grep -o '[0-9\.]\+')
ELAPSED_WITH_ICECREAM=$(grep '^Elapsed time:' $RESULTS_DIR/with-icecream/build_stats | grep -o '[0-9\.]\+')
CPU_WITHOUT_ICECREAM=$(grep '^CPU usage:' $RESULTS_DIR/without-icecream/build_stats | grep -o '[0-9\.]\+')
CPU_WITH_ICECREAM=$(grep '^CPU usage:' $RESULTS_DIR/with-icecream/build_stats | grep -o '[0-9\.]\+')

ELAPSED_DELTA="$(echo "scale=1; $ELAPSED_WITH_ICECREAM - $ELAPSED_WITHOUT_ICECREAM" | bc)"
ELAPSED_SPEEDUP="$(echo "scale=2; $ELAPSED_DELTA * 100 / $ELAPSED_WITHOUT_ICECREAM" | bc)"

CPU_DELTA="$(echo "scale=1; $CPU_WITH_ICECREAM - $CPU_WITHOUT_ICECREAM" | bc)"
CPU_SPEEDUP="$(echo "scale=2; $CPU_DELTA * 100 / $CPU_WITHOUT_ICECREAM" | bc)"

cat <<HEREDOC > $RESULTS_DIR/elapsed.txt
               $(printf "%8s" "ABSDIFF")  $(printf "%8s" "RELDIFF")  $(printf "%8s" "ELAPSED1") -> ELAPSED2
Elapsed time: $(printf "%8s" $ELAPSED_DELTA)s $(printf "%8s" $ELAPSED_SPEEDUP)% $(printf "%8s" $ELAPSED_WITHOUT_ICECREAM)s -> ${ELAPSED_WITH_ICECREAM}s
CPU usage:    $(printf "%8s" $CPU_DELTA)% $(printf "%8s" $CPU_SPEEDUP)% $(printf "%8s" $CPU_WITHOUT_ICECREAM)% -> $CPU_WITH_ICECREAM%
HEREDOC

