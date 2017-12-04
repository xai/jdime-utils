#!/usr/bin/env python3
#
# Copyright (C) 2017 Olaf Lessenich

import argparse
import csv
import os
import sys
import tempfile
from plumbum import colors
from plumbum import local


GIT = local['git']
STRATEGY = '$$STRATEGY$$'

def run(job):
    project = job['project']
    left = job['left'][0:7]
    right = job['right'][0:7]
    file = job['file']
    strategies = job['strategies'].split(',')
    for strategy in strategies:
        print('%s %s %s %s %s: ' % (project, left, right, file, strategy), end='')
        cmd = job['cmd'].replace(STRATEGY, strategy).split(' ')
        exe = cmd[0]
        args = cmd[1:]

        ret, stdout, stderr = local[exe][args].run(retcode=None)
        if ret == 0:
            print(colors.green & colors.bold | 'OK')
        else:
            print(colors.green & colors.bold | ('FAILED (%d)' % ret))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('-p', '--prune',
                        help='Prune successfully merged scenarios',
                        action="store_true")
    parser.add_argument('commits', default=[], nargs='+')
    args = parser.parse_args()

    if args.output:
        target = args.output
    else:
        target = tempfile.mkdtemp(prefix="jdime.")

    cols = ['project', 'left', 'right', 'file', 'strategies', 'cmd']
    for job in csv.DictReader(iter(GIT['preparemerge', '-o', target,
                                       args.commits[0]]().splitlines()),
                              delimiter=';',
                              fieldnames=cols):
        run(job)

if __name__ == "__main__":
    main()
