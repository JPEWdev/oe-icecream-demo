#! /usr/bin/env python3
#
# Copyright 2019 Garmin Ltd. or its subsidiaries
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import glob
import re
from scipy import stats
import numpy

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(THIS_DIR, 'poky', 'scripts', 'lib'))

from buildstats import BuildStats, diff_buildstats, taskdiff_fields, BSVerDiff

ICECREAM_TASKS = ('do_compile', 'do_compile_kernelmodules', 'do_configure', 'do_install')
VALUES = ('cputime', 'walltime')

def sum_task_totals(bs):
    d = {}
    for recipe_data in bs.values():
        for name, bs_task in recipe_data.tasks.items():
            for val_type in VALUES:
                val = getattr(bs_task, val_type)
                key = (name, val_type)
                if name not in ICECREAM_TASKS:
                    key = ('other', val_type)

                d.setdefault(key, 0)
                d[key] += val

                key = ('overall', val_type)
                d.setdefault(key, 0)
                d[key] += val

    return d

def get_elapsed(p):
    elapsed = None
    cpu = None

    with open(os.path.join(p, 'build_stats'), 'r') as f:
        for l in f:
            m = re.match(r'Elapsed time: (?P<elapsed>[\d.]+) ', l)
            if m is not None:
                elapsed = float(m.group('elapsed'))
                continue

            m = re.match(r'CPU usage: (?P<cpu>[\d.]+)%', l)
            if m is not None:
                cpu = float(m.group('cpu')) / 100

    if elapsed is None:
        raise Exception('Elapsed time not found for %s' % p)

    if cpu is None:
        raise Exception('CPU usage not found for %s' % p)

    return (elapsed, cpu)

def pooled_stdev(a_std_dev, b_std_dev):
    return numpy.sqrt((a_std_dev**2 + b_std_dev**2)/2)

def write_elapsed():
    with open(os.path.join(THIS_DIR, 'stats', 'elapsed.csv'), 'w') as f:
        f.write('Build,Elapsed without Icecream,Elapsed with Icecream,CPU usage without Icecream,CPU usage with Icecream\n')
        elapsed_combined_without = []
        elapsed_combined_with = []
        cpu_combined_without = []
        cpu_combined_with = []

        for p in glob.glob(os.path.join(THIS_DIR, 'stats', 'build*')):
            without_elapsed, without_cpu = get_elapsed(os.path.join(p, 'without-icecream'))
            with_elapsed, with_cpu = get_elapsed(os.path.join(p, 'with-icecream'))

            elapsed_combined_without.append(without_elapsed)
            elapsed_combined_with.append(with_elapsed)

            cpu_combined_without.append(without_cpu)
            cpu_combined_with.append(with_cpu)

            f.write('%s,%f,%f,%f,%f\n' % (os.path.basename(p), without_elapsed, with_elapsed,
                                                without_cpu, with_cpu))

        f.write('\n')
        f.write(',Average without Icecream (s),Without Icecream std dev,Average with Icecream (s),With Icecream std dev,p-value,Percent Change,Percent Change std dev\n')
        average_without = numpy.average(elapsed_combined_without)
        average_with = numpy.average(elapsed_combined_with)
        without_std_dev = numpy.std(elapsed_combined_without)
        with_std_dev = numpy.std(elapsed_combined_with)
        change = (average_with - average_without) / average_without
        pooled_std_dev = pooled_stdev(without_std_dev, with_std_dev) / average_without
        _, p = stats.ttest_rel(elapsed_combined_without, elapsed_combined_with)
        f.write('Elapsed Time,%f,%f,%f,%f,%e,%.2f,%f\n' % (
            average_without, without_std_dev,
            average_with, with_std_dev, p,
            change, pooled_std_dev))

        f.write('\n')
        f.write(',Average without Icecream,Without Icecream std dev,Average with Icecream,With Icecream std dev,p-value,Delta\n')
        average_without = numpy.average(cpu_combined_without)
        average_with = numpy.average(cpu_combined_with)
        without_std_dev = numpy.std(cpu_combined_without)
        with_std_dev = numpy.std(cpu_combined_with)
        delta = average_with - average_without
        _, p = stats.ttest_rel(cpu_combined_without, cpu_combined_with)
        f.write('CPU Usage,%f,%f,%f,%f,%e,%.2f\n' % (
            average_without, without_std_dev,
            average_with, with_std_dev, p,
            delta))

def write_tasks():
    with open(os.path.join(THIS_DIR, 'stats', 'raw.csv'), 'w') as f:
        combined_with = {}
        combined_without = {}
        f.write('Task,Attribute,Build,Without Icecream,With Icecream\n')
        for p in glob.glob(os.path.join(THIS_DIR, 'stats', 'build*')):
            without_stats = BuildStats.from_dir(os.path.join(p, 'without-icecream'))
            with_stats = BuildStats.from_dir(os.path.join(p, 'with-icecream'))

            without_d = sum_task_totals(without_stats)
            with_d = sum_task_totals(with_stats)

            for k in without_d.keys():
                without_val = without_d[k]
                with_val = with_d[k]
                f.write("%s,%s,%s,%f,%f\n" % (k[0], k[1], os.path.basename(p), without_val, with_val))

                combined_with.setdefault(k, []).append(with_val)
                combined_without.setdefault(k, []).append(without_val)

    with open(os.path.join(THIS_DIR, 'stats', 'totals.csv'), 'w') as f:
        f.write('Task,Attribute,Without Icecream,Without Std dev,With Icecream,With Std dev,p-value,Percent Change,Percent Change Std Dev\n')
        for k in combined_without.keys():
            without_avg = numpy.average(combined_without[k])
            with_avg = numpy.average(combined_with[k])
            without_std_dev = numpy.std(combined_without[k])
            with_std_dev = numpy.std(combined_with[k])
            change = (with_avg - without_avg) / without_avg
            pooled_std_dev = pooled_stdev(without_std_dev, with_std_dev) / without_avg
            _, p = stats.ttest_rel(combined_without[k], combined_with[k])
            f.write("%s,%s,%f,%f,%f,%f,%e,%.2f,%f\n" % (k[0], k[1], without_avg, without_std_dev, with_avg, with_std_dev, p, change, pooled_std_dev))

def main():
    write_tasks()
    write_elapsed()

if __name__ == "__main__":
    main()


# exit on any error and unset variables
#set -u -e -o pipefail

#THIS_DIR="$(readlink -f $(dirname $0))"
#
#TASKS="do_configure do_compile do_install do_package_write_rpm"
#ATTRS="cputime walltime"
#
#echo "Task,Attribute,Build,Without Icecream,With Icecream" > $THIS_DIR/stats/stat.csv
#
#for d in $THIS_DIR/stats/build*; do
#    for task in $TASKS; do
#        for attr in $ATTRS; do
#            VAL="$($THIS_DIR/poky/scripts/buildstats-diff --only-task $task --diff-attr $attr $d/without-icecream $d/with-icecream | tail -1)"
#            echo "$task,$attr,$d,$(echo $VAL | sed 's/.*(\([0-9.]\+\)s).*(\([0-9.]\+\)s).*/\1,\2/g')" >> $THIS_DIR/stats/stat.csv
#        done
#    done
#done
