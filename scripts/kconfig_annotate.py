#!/usr/bin/python3

import os
import os.path
import re
import sys

# A very crude kconfig menu parser

MENU_NAME_RE = re.compile(r'^arch/([^/]+)/')
MENU_LINE_RE = re.compile(r'^(\s*)(?:(?:--+\s*)?(\w+)(?:\s*--+)?(?:\s+(.*))?)?')

def parse_menu(root, filename, files_parsed, symbol_map):
    if filename in files_parsed:
        return

    match = MENU_NAME_RE.match(filename)
    arch = match and match.group(1)

    help_indent = None
    with open(os.path.join(root, filename), encoding='utf-8') as f:
        for line in f:
            match = MENU_LINE_RE.match(line)
            assert match
            indent = len(match.group(1))
            if help_indent is not None:
                if indent > help_indent:
                    help_indent = indent
                if indent >= help_indent or not match.group(2):
                    continue

            keyword, rest = match.group(2, 3)
            help_indent = None
            if keyword == 'source':
                parse_menu(root, rest.strip('"'), files_parsed, symbol_map)
            elif keyword == 'help':
                help_indent = indent
            elif keyword in ['config', 'menuconfig']:
                symbol_map[(rest.strip(), arch)] = filename

    files_parsed.add(filename)

KCONFIG_ENABLE_RE = re.compile(r'^CONFIG_(\w+)=[ym]')

def main(ksrc, *kconfigs):
    files_parsed = set()
    symbol_map = {}
    enabled_map = {}

    for kconfig in kconfigs:
        arch = kconfig.split(os.sep)[1]
        top_menu = os.path.join('arch', arch, 'Kconfig')
        parse_menu(ksrc, top_menu, files_parsed, symbol_map)

        with open(kconfig) as f:
            for line in f:
                match = KCONFIG_ENABLE_RE.match(line)
                if match:
                    symbol = match.group(1)
                    menu = symbol_map.get((symbol, None)) or symbol_map.get((symbol, arch))
                    if not menu:
                        print('W: could not find %s' % symbol, file=sys.stderr)
                        menu = '<unknown>'
                    enabled_map.setdefault(menu, set()).add(symbol)

    for menu in sorted(enabled_map.keys()):
        print('[%s]' % menu)
        for symbol in sorted(enabled_map[menu]):
            print('CONFIG_%s' % symbol)
        print('')

if __name__ == '__main__':
    main(*sys.argv[1:])
