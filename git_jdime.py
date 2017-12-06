#!/usr/bin/env python3
#
# Copyright (C) 2017 Olaf Lessenich

import argparse
import csv
import os
import tempfile
from plumbum import colors
from plumbum import local


GIT = local['git']
STRATEGY = '$$STRATEGY$$'
COLS = ['project', 'left', 'right', 'file', 'strategies', 'target', 'cmd']

def get_merge_commits():
    return GIT['rev-list', '--all', '--merges']().splitlines()

def get_jobs(target, commits):
    return csv.DictReader(iter(GIT['preparemerge', '-o', target, commits]()\
                               .splitlines()), delimiter=';', fieldnames=COLS)

def run(job, prune, srcfile=None):
    project = job['project']
    left = job['left'][0:7]
    right = job['right'][0:7]
    file = job['file']
    target = job['target']

    fail = False

    if not srcfile or srcfile == file:
        errorlog = os.path.join(target, 'error.log')
        strategies = job['strategies'].split(',')
        for strategy in strategies:
            scenario = '%s %s %s %s %s' % (project, left, right, file, strategy)
            print('%s: ' % scenario, end='')
            cmd = job['cmd'].replace(STRATEGY, strategy).split(' ')
            exe = cmd[0]
            args = cmd[1:]

            ret, stdout, stderr = local[exe][args].run(retcode=None)
            if ret == 0:
                print(colors.green | 'OK')
            else:
                fail = True
                print(colors.red | ('FAILED (%d)' % ret))
                with open(errorlog, 'a') as err:
                    err.write(80 * '=' + '\r\n')
                    err.write(scenario + '\r\n')
                    err.write('> %s\r\n' % ' '.join(cmd))
                    err.write(80 * '-' + '\r\n')
                    err.writelines(stderr)
                    err.write(80 * '-' + '\r\n')

    if prune and not fail:
        for root, dirs, files in os.walk(target, topdown=False):
            for f in files:
                path = os.path.join(root, f)
                if path.endswith(file):
                    os.remove(path)
            if not os.listdir(root):
                os.rmdir(root)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('-f', '--file',
                        help='Merge only specified file',
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

    commits = args.commits

    if len(commits) == 1 and commits[0] == 'all':
        for commit in get_merge_commits():
            for job in get_jobs(target, [commit,]):
                run(job, args.prune, args.file)
    else:
        for job in get_jobs(target, commits):
            run(job, args.prune, args.file)

    if args.prune and not os.listdir(target):
        os.rmdir(target)
    else:
        print()
        if args.prune:
            stored = 'Erroneous'
        else:
            stored = 'All'
        print('%s merge scenarios have been stored to %s' % (stored, target))

if __name__ == "__main__":
    main()
