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
        'mergetype',
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
        if row['mergetype'] == 'skipped':
            # print('%s %s %s SKIPPED (%s)' % (row['project'],
                                             # row['mergecommit'],
                                             # row['file'],
                                             # row['strategy']))
            return

        scenario = '%s %s %s %s %s %s %s %.4f' % (row['project'], row['timestamp'],
                                                  row['mergecommit'], row['left'],
                                                  row['right'], row['file'],
                                                  row['strategy'], float(row['runtime']))
        if row['mergetype'].startswith('FAIL'):
            c = colors.red
            msg = row["mergetype"]
        elif int(row['conflicts']) > 0 or int(row['parsed_conflicts']) > 0:
            if int(row['conflicts']) != int(row['parsed_conflicts']):
                c = colors.cyan
                msg = "MISMATCH"
            else:
                c = colors.blue
                msg = "OK"
            msg += (' (%d/%d conflicts, %d lines, %d tokens)' %
                   (int(row['parsed_conflicts']),
                    int(row['conflicts']),
                    int(row['clines']),
                    int(row['ctokens'])))
        else:
            c = colors.green
            msg = "OK"


        print(c | '%s: ' % scenario, end='')
        print(c | msg, end='')

        if row['mergetype'] == '2-way':
            print(colors.magenta | (' %s' % row['mergetype']))
        else:
            print()

    except ValueError:
        # probably csv header
        pass

def main():
    for row in csv.DictReader(iter(sys.stdin.readline, ''), delimiter=';', fieldnames=COLS):
        colorize(row)

if __name__ == "__main__":
    main()
