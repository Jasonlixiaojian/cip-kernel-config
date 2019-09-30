#!/usr/bin/python3

# Copyright 2019 Codethink Ltd.
#
# This script is distributed under the terms and conditions of the GNU General
# Public License, Version 3 or later. See http://www.gnu.org/copyleft/gpl.html
# for details.

import posixpath
import re
import sys

import yaml
import yaml.loader


KCONFIG_ENABLE_RE = re.compile(r'^(CONFIG_\w+)=[ym]')


def load_unsup(name):
    with open(name, 'r', encoding='utf-8') as f:
        unsup = yaml.safe_load(f)

    unsup_symbols = {}
    unsup_paths = {}

    for entry in unsup:
        desc = entry['description']
        for symbol in entry.get('symbols', []):
            unsup_symbols[symbol] = desc
        for path in entry.get('paths', []):
            # When checking paths, we will generate directory names without
            # trailing slashes, so strip them off here
            unsup_paths[path] = desc.rstrip('/')

    return unsup_symbols, unsup_paths


def check_symbols(name, unsup):
    with open(name, 'r', encoding='utf-8') as f:
        for line in f:
            match = KCONFIG_ENABLE_RE.match(line)
            if match:
                symbol = match.group(1)
                if symbol in unsup:
                    print('%s: %s: %s' %
                          (name, symbol, unsup[symbol]))


# We can only reliably tell whether C and assembly sources are used, so don't
# warn about other files as this will produce false positives
SOURCE_CHECK_RE = re.compile(r'\.[chS]$')


def check_sources(name, unsup):
    warned = set()

    with open(name, 'r', encoding='utf-8') as f:
        for line in f:
            path = line.rstrip()

            if not SOURCE_CHECK_RE.search(path):
                continue

            # Check the file name and all ancestors
            while path:
                if path in warned:
                    # Don't repeat the warning for multiple files in dir
                    break
                if path in unsup:
                    print('%s: %s: %s' %
                          (name, path, unsup[path]))
                    warned.add(path)
                path = posixpath.dirname(path)


def main(unsup_name, config_name, sources_name):
    unsup_symbols, unsup_sources = load_unsup(unsup_name)
    check_symbols(config_name, unsup_symbols)
    check_sources(sources_name, unsup_sources)


if __name__ == '__main__':
    main(*sys.argv[1:])
