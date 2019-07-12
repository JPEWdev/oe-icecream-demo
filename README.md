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

[Icecream]: https://github.com/icecc/icecream
[pyrex]: https://github.com/garmin/pyrex
