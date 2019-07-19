
This repository provides kernel configurations for various boards in
use in CIP project. Some config files do not provide answers to all
the config questions; in such case just accept default value, for
example by using `yes '' | make oldconfig`.

Mapping between boards in Lava test lab and config files is as follows:

| Board     | Config file                     |
|-----------|-------------|
| iwg20m    | arm/renesas_shmobile_defconfig  |