#!/usr/bin/python3

# Copyright 2019 Codethink Ltd.
#
# This script is distributed under the terms and conditions of the GNU General
# Public License, Version 3 or later. See http://www.gnu.org/copyleft/gpl.html
# for details.

import os
import os.path
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile


arch_re = re.compile(r'^arch/([^/]+)/.')


def copy_config(kconfig, build_dir, source_dir):
    # We don't copy the config exactly as-is, but remove references
    # to any missing files.

    string_set_re = re.compile(r'^(CONFIG_(?:\w+))="(.*)"$')
    xfile_sym_types = {
        # symbol                               multi-value?  directory symbol
        'CONFIG_MODULE_SIG_KEY':              (False,        None),
        'CONFIG_SYSTEM_TRUSTED_KEYS':         (False,        None),
        'CONFIG_SYSTEM_BLACKLIST_HASH_LIST':  (False,        None),
        'CONFIG_ACPI_CUSTOM_DSDT_FILE':       (False,        None),
        'CONFIG_EXTRA_FIRMWARE':              (True,  'CONFIG_EXTRA_FIRMWARE_DIR'),
        'CONFIG_EXTRA_FIRMWARE_DIR':          (False,        None),
        'CONFIG_CFG80211_EXTRA_REGDB_KEYDIR': (False,        None),
        'CONFIG_INITRAMFS_SOURCE':            (True,         None)
        }
    xfile_sym_values = {}

    # We have to do two passes over the file because we need to see
    # the value of CONFIG_EXTRA_FIRMWARE_DIR before validating
    # CONFIG_EXTRA_FIRMWARE

    # Extract all filenames
    with open(kconfig) as f_in:
        for line in f_in:
            match = string_set_re.search(line)
            if not match:
                continue
            name, value = match.group(1, 2)
            try:
                multi, _ = xfile_sym_types[name]
            except KeyError:
                continue
            if multi:
                xfile_sym_values[name] = value.split()
            else:
                xfile_sym_values[name] = [value]

    # Remove references to missing files
    for name, filenames in xfile_sym_values.items():
        if not filenames:
            # If CONFIG_EXTRA_FIRMWARE is empty, CONFIG_EXTRA_FIRMWARE_DIR
            # will not even be present in the config file and we must
            # avoid looking it up.  In any case, we never need to modify
            # an empty value.
            continue

        _, dir_sym_name = xfile_sym_types[name]
        if dir_sym_name:
            base_dir = os.path.join(source_dir, xfile_sym_values[dir_sym_name][0])
        else:
            base_dir = source_dir
        new_filenames = []
        for filename in filenames:
            if name == 'CONFIG_MODULE_SIG_KEY' \
               and filename == 'certs/signing_key.pem':
                # Special case: this file is automatically created
                new_filenames.append(filename)
            elif os.path.exists(os.path.join(base_dir, filename)):
                new_filenames.append(filename)
            else:
                print('W: Removing missing file "%s" from value of %s'
                      % (filename, name),
                      file=sys.stderr)
        xfile_sym_values[name] = new_filenames

    # Copy file, replacing values as necessary
    with open(kconfig) as f_in, \
         open(os.path.join(build_dir, '.config'), 'w') as f_out:
        for line in f_in:
            match = string_set_re.search(line)
            if match:
                name, _ = match.group(1, 2)
                if name in xfile_sym_values:
                    line = '%s="%s"\n' % (name, ' '.join(xfile_sym_values[name]))
            f_out.write(line)


def find_c_asm_sources(source_dir, kconfig, *makeflags):
    source_dir_abs = os.path.abspath(source_dir)

    sources = set()

    # Clean source tree.  Redirect stdout to our stderr, so that it
    # doesn't interfere with our own output.
    subprocess.run(['make'] + list(makeflags) + ['mrproper'],
                   cwd=source_dir, stdout=sys.stderr, close_fds=False, check=True)

    # Parse make arguments
    make_var_re = re.compile(r'^(\w[\w\-]+)=(.*)$', re.DOTALL)
    make_vars = {}
    make_opts = []
    for arg in makeflags:
        match = make_var_re.search(arg)
        if match:
            make_vars[match.group(1)] = match.group(2)
        else:
            make_opts.append(arg)

    srcarch = make_vars.get('ARCH')

    # Insert wrapper script into make variables
    wrapper = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'get_used_sources_wrapper')
    cross_compile = make_vars.get('CROSS_COMPILE', '')
    make_vars['AS'] = wrapper + ' ' + make_vars.get('AS', cross_compile + 'as')
    make_vars['CC'] = wrapper + ' ' + make_vars.get('CC', cross_compile + 'gcc')
    make_vars['HOSTCC'] = wrapper + ' ' + make_vars.get('HOSTCC', 'gcc')

    # Build in temporary directory
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR', '/var/tmp')) \
         as build_dir, \
         tempfile.NamedTemporaryFile(mode='w+') as makefile:
        build_dir_abs = os.path.abspath(build_dir)
        make_vars['O'] = build_dir_abs

        env = os.environ.copy()
        env['KERNEL_CONFIG_MAKEFILE'] = makefile.name

        # Regenerate make arguments
        makeflags = make_opts + ['%s=%s' % item for item in make_vars.items()]

        copy_config(kconfig, build_dir, source_dir)

        # Redirect stdout to our stderr, so that it doesn't interfere with
        # our own output
        subprocess.run(['make'] + makeflags + ['oldconfig'],
                       cwd=source_dir, env=env, stdin=subprocess.DEVNULL,
                       stdout=sys.stderr, close_fds=False, check=True)
        subprocess.run(['make'] + makeflags,
                       cwd=source_dir, env=env, stdin=subprocess.DEVNULL,
                       stdout=sys.stderr, close_fds=False, check=True)

        make_deps_re = re.compile(r'^(?:[^\s:]+::?)?\s*(.*?)\s*\\?\n')

        for line in makefile:
            # Parse line to find dependencies
            match = make_deps_re.search(line)
            if not match:
                print("W: could not parse dependency line:", line,
                      file=sys.stderr, end='')
                continue

            for name in match.group(1).split():
                # Get absolute filename
                name = os.path.normpath(os.path.join(build_dir_abs, name))

                # Exclude files outside source tree (either generated or
                # system headers)
                if os.path.commonpath([source_dir_abs, name]) \
                   != source_dir_abs:
                    continue

                # Get source-relative filename
                name = os.path.relpath(name, source_dir_abs)

                # Convert to POSIX filename format
                name = name.replace(os.sep, '/')

                # Infer srcarch from the first file found under arch/
                if srcarch is None:
                    match = arch_re.search(name)
                    if match:
                        srcarch = match.group(1)

                sources.add(name)

    return sources, srcarch


# Find additional source files that might (conservatively) be needed
def find_other_sources(source_dir, srcarch):
    sources = set()

    lstree_re = re.compile(r'^[0-7]{6} (blob|tree) [0-9a-f]{40,}\t(.*)\n')
    ignore_re = re.compile(r'(?:^|/)\.'                     # configuration
                           r'|\.[chS]$'                     # C/asm source file
                           r'|^(?:Documentation|samples)/'  # documentation
                           r'|^tools/(?!objtool/)')         # user-space

    with subprocess.Popen(['git', 'ls-tree', '-r', 'HEAD'], cwd=source_dir,
                          stdout=subprocess.PIPE, universal_newlines=True) \
                          as list_proc:
        for line in list_proc.stdout:
            # Parse line to find object type and name
            match = lstree_re.search(line)
            if not match:
                print("W: could not parse ls-tree line:", line,
                      file=sys.stderr, end='')
                continue
            objtype, name = match.group(1, 2)
            basename = posixpath.basename(name)

            # Exclude directories
            if objtype != 'blob':
                continue

            # Exclude files from other architectures - we assume that only
            # C sources are re-used cross-architecture
            match = arch_re.search(name)
            if match and match.group(1) != srcarch:
                continue

            # Exclude various ignoreable patterns
            if ignore_re.search(name):
                continue

            sources.add(name)

    return sources


def main(source_dir, kconfig, *makeflags):
    sources, srcarch = find_c_asm_sources(source_dir, kconfig, *makeflags)
    sources |= find_other_sources(source_dir, srcarch)

    for name in sorted(list(sources)):
        print(name)


if __name__ == '__main__':
    main(*sys.argv[1:])
