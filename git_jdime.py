#!/usr/bin/env python3
#
# Copyright (C) 2017 Olaf Lessenich

import argparse
import csv
import os
import sys
import tempfile
from plumbum import local


GIT = local['git']
STRATEGY = '$$STRATEGY$$'

def run(job):
    project = job['project']
    left = job['left'][0:7]
    right = job['right'][0:7]
    file = job['file']
    strategies = job['strategies'].split(',')
    cmd = job['cmd']
    for strategy in strategies:
        print('%s %s %s %s %s' % (project, left, right, file, strategy))
        print(cmd.replace(STRATEGY, strategy))

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
