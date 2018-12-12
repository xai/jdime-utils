#!/usr/bin/env python3
#
# Copyright © 2018 Olaf Lessenich <xai@linux.com>

import csv
import sys
from plumbum import colors

COLS = ['project', 'left', 'right', 'file', 'strategy', 'conflicts']

def colorize(row):
    scenario = '%s %s %s %s %s' % (row['project'], row['left'], row['right'],
                              row['file'], row['strategy'])
    print('%s: ' % scenario, end='')
    if int(row['conflicts']) > 0:
        print(colors.cyan | ('OK (%d conflicts)' % int(row['conflicts'])))
    else:
        print(colors.green | 'OK')

def main():
    for row in csv.DictReader(iter(sys.stdin.readline, ''), delimiter=';', fieldnames=COLS):
        colorize(row)

if __name__ == "__main__":
    main()
