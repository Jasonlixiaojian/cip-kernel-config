# cip-kernel-config - Linux kernel configurations for CIP

This repository provides kernel configurations for various boards in
use in CIP project. Some config files do not provide answers to all
the config questions; in such case just accept default value, for
example by using `yes '' | ARCH=xxx make oldconfig`.

## Usage with Lava

Mapping between boards in Lava test lab and config files is as follows:

<table>
<tr><th>Alias   <th>Device type in Lava     <th>Config file
<tr><td>iwg20m  <td>r8a7743-iwg20d-q7       <td>arm/renesas_shmobile_defconfig
<tr><td>socfpga <td>Altera-Terasic-Deo-Nano <td>arm/socfgpa_defconfig
</table>

List of device types is at <https://lava.ciplatform.org/scheduler/device_types>.
