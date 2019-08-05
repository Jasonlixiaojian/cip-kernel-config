# cip-kernel-config - Linux kernel configurations for CIP

This repository provides kernel configurations for various boards in
use in CIP project. Some config files do not provide answers to all
the config questions; in such case just accept default value, for
example by using `yes '' | ARCH=xxx make oldconfig`.

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

## Usage with Lava

Mapping between boards in Lava test lab and config files is as follows:

<table>
<tr><th>Alias   <th>Device type in Lava     <th>Config file
<tr><td>iwg20m  <td>r8a7743-iwg20d-q7       <td>arm/renesas_shmobile_defconfig
<tr><td>socfpga <td>Altera-Terasic-Deo-Nano <td>arm/socfgpa_defconfig
</table>

List of device types is at <https://lava.ciplatform.org/scheduler/device_types>.
