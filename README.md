# cip-kernel-config - Linux kernel configurations for CIP

This repository provides kernel configuration files and source lists
for various boards in use in CIP project. Some config files do not
provide answers to all the config questions; in such case just accept
default value, for example by using `yes '' | ARCH=xxx make
oldconfig`.

## Configuration file types

The configuration files may be provided as either:

* Minimised configuration (like in `arch/*/configs`).  This is
  preferred.  These files have a `_defconfig` suffix.
* Full configuration (like `.config`).  These have a `.config` suffix.

The `Makefile` has rules for converting between these two formats.
However, all full configuration files need to be explicitly listed
in the `CONFIG_SRC` variable.  The minimised configuration files
generated from them should also be listed in the appropriate
`.gitignore` file.

## Directory layout

In the root of the repository there is a subdirectory for each
maintained CIP kernel branch, with the `linux-` prefix omitted.  For
example, configurations for the `linux-4.4.y-cip` branch are under the
`4.4.y-cip` subdirectory.

In each of those there is a subdirectory for each architecture that's
used, using kernel source architecture names.  For example, all x86
configurations are under `x86` but Arm configurations are split
between `arm` (32-bit) and `arm64` (64-bit).

All configuration files must be added in the appropriate architecture
subdirectory of the appropriate branch subdirectory.

## Generated files

The `Makefile` contains rules to generate:

* Full configuration files from minimised configuration files, and
  vice versa.
* A list of all enabled config symbols per branch
  (*branch*`/all-enabled`).
* A list of potentially used source files per configuration
  (*branch*`/`*arch*`/`*config-name*`.sources`).
* A list of all potentially used source files per branch
  (*branch*`/all.sources`).

The `all` target will (re)generate the first two groups of files,
and the `clean` target will remove them.

Generating a list of used source files requires running a complete
kernel build process, which can take hours for the full set of
configurations.  For this reason, the source file lists are committed
to git and will only be (re)generated by the `all_sources` target.
The `clean_sources` target will remove all generated files.

## Usage with Lava

Mapping between boards in Lava test lab and config files is as follows:

| Alias   | Device type in Lava     | Config file                    |
| ---     | ---                     | ---                            |
| iwg20m  | r8a7743-iwg20d-q7       | arm/renesas_shmobile_defconfig |
| socfpga | Altera-Terasic-Deo-Nano | arm/socfgpa_defconfig          |

List of device types is at <https://lava.ciplatform.org/scheduler/device_types>.

## Warnings

Each kernel branch should have rules for warning about configuration
symbols that are not security supportable or not recommended for other
reasons, in a YAML file called `warnings.yml`.  This is structured as
a sequence of mappings, where each mapping can have the keys:

* `description` (required): Short description of the feature and what
  the problem is with it
* `symbols` (optional): Kernel config symbols associated with the
  feature
* `paths` (optional): Kernel source file or directory names
  associated with the feature

The `show_warnings.py` script will show the relevant warnings.  Its
arguments are: the warnings file name, the config file name, and the
sources list file name.
