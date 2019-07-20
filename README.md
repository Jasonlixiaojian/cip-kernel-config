
This repository provides kernel configurations for various boards in
use in CIP project. Some config files do not provide answers to all
the config questions; in such case just accept default value, for
example by using `yes '' | ARCH=xxx make oldconfig`.

Mapping between boards in Lava test lab and config files is as follows:

| Alias   | Device type in Lava     | Config file                    |
| iwg20m  | r8a7743-iwg20d-q7       | arm/renesas_shmobile_defconfig |
| socfpga | Altera-Terasic-Deo-Nano | arm/socfgpa_defconfig          |

List of device types is at https://lava.ciplatform.org/scheduler/device_types .
