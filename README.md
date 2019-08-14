# OpenEmbedded Icecream Build Test

Does test builds using Yocto/OpenEmbedded with and without [Icecream][] and
shows the build improvement.

## Requirements

1. A properly configured Icecream cluster
2. Docker. This build uses [pyrex][] to reduce build host differences

## Configuring the build

The default configuration used by the test should be sufficient for most
testing cases. If customizing the way icecream is configured is desired, you
can edit the [local.conf.sample][./conf/with-icecream/local.conf.sample] file.
Notable things to change are:

* `ICECC_PARALLEL_MAKE` This will control how many parallel compiles are
  performed when Icecream is enabled. It is generally recommended to be 3x to
  4x the number of CPU cores you have
* `ICECC_USER_PACKAGE_BL` This controls which recipes are blacklisted by
  icecream. You may need to add more if there are recipes that fail to compile
  with icecc.

## Running the test

The following command will initiate the test:

```shell
./test_icecream.sh
```

The test will take a few hours (since it does two builds from scratch). You
should leave your computer alone while running the test so as not to introduce
error in the test.

## Viewing the results

The results of the build will be available in the `results/` output directory.
The full buildstats for each build are available, as well as a summary report
that shows build time changes for both CPU time, wall clock time, and elapsed
time.

*NOTE:* The CPU time an wall clock time totals are summed over all bitbake
tasks, and thus totals will probably be larger than expected since multiple
tasks are executing in parallel. The elapsed time results gives an accurate
summary of how much the actual build time changed (e.g. how long you actually
had to wait for the build).

## Running a statistical analysis

A statistical analysis of the impact that Icecream has on the build can be
captured using the `build_stats.sh` script. The script takes up to two
arguments, optionally the starting build number, and the ending build number.
This allows you to split up builds you want to perform into multiple
invocations. For example, to run 20 tests which will create results for builds
numbered 1-20.

```shell
./build_stats.sh 20
```

You can also split this up into two phases of 10 builds each if desired:

```shell
./build_stats.sh 10
./bulld_stats.sh 11 20
```

Once the builds are complete, the results can be analyzed using the
`analyze_stats.py` script. The script will detect the output from all test runs
built with `build_stats.sh` and generate a number of CSV spreadsheet files in
the `stats` directory as output.

*Note:* The `analyze_stats.py` script requires that both
[numpy](https://www.numpy.org/) and [scipy](https://www.scipy.org/) are
installed

[Icecream]: https://github.com/icecc/icecream
[pyrex]: https://github.com/garmin/pyrex
