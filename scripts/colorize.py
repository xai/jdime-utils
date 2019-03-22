#!/usr/bin/env python3
#
# Copyright © 2018 Olaf Lessenich <xai@linux.com>

import csv
import sys
from plumbum import colors

COLS = ['project',
        'timestamp',
        'mergecommit',
        'left',
        'right',
        'file',
        'strategy',
        'conflicts',
        'clines',
        'ctokens',
        'parsed_conflicts',
        'runtime',
        't_merge',
        't_parse',
        't_semistructure',
        't_LinebasedStrategy',
        't_SemiStructuredStrategy',
        't_StructuredStrategy',
        'jdimeversion']

def colorize(row):
    try:
        scenario = '%s %s %s %s %s %s %s %.4f' % (row['project'], row['timestamp'],
                                             row['mergecommit'], row['left'],
                                             row['right'], row['file'],
                                             row['strategy'], float(row['runtime']))
        print('%s: ' % scenario, end='')
        if int(row['conflicts']) > 0 or int(row['parsed_conflicts']) > 0:
            print(colors.cyan | ('OK (%d/%d conflicts, %d lines, %d tokens)' %
                                 (int(row['parsed_conflicts']),
                                  int(row['conflicts']),
                                  int(row['clines']),
                                  int(row['ctokens']))))
        else:
            print(colors.green | 'OK')
    except ValueError:
        # probably csv header
        pass

def main():
    for row in csv.DictReader(iter(sys.stdin.readline, ''), delimiter=';', fieldnames=COLS):
        colorize(row)

if __name__ == "__main__":
    main()
