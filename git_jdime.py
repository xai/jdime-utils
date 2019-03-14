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
from plumbum.cmd import grep
from plumbum.commands.processes import ProcessExecutionError


GIT = local['git']
STRATEGY = '$$STRATEGY$$'
COLS = ['project', 'merge', 'left', 'right', 'file', 'strategies', 'target', 'cmd']

def get_merge_commits():
    return GIT['rev-list', '--all', '--merges']().splitlines()

def get_jobs(target, noop=False, commits=[]):
    options = ["-o", target]
    if noop:
        options.append("-n")
    return csv.DictReader(iter(GIT['preparemerge', options, commits]()\
                               .splitlines()), delimiter=';', fieldnames=COLS)

def count_conflicts(merged_file):
    conflicts = 0

    try:
        conflicts = int(grep['-c', '-e', '^<<<<<<<', merged_file]().strip())
    except ProcessExecutionError:
        pass

    return conflicts

def run(job, prune, writer, srcfile=None, noop=False):

    if noop:
        writer = csv.DictWriter(sys.stdout, delimiter=';', fieldnames=COLS)
        writer.writerow(job)
        return

    project = job['project']
    mergecommit = job['merge'][0:7]
    left = job['left'][0:7]
    right = job['right'][0:7]
    file = job['file']
    target = job['target']

    fail = False

    if not srcfile or srcfile == file:
        errorlog = os.path.join(target, 'error.log')
        strategies = job['strategies'].split(',')
        for strategy in strategies:
            scenario = '%s %s %s %s %s %s' % (project, mergecommit, left, right, file, strategy)
            cmd = job['cmd'].replace(STRATEGY, strategy).split(' ')
            exe = cmd[0]
            args = cmd[1:]
            outfile = args[6]

            ret, stdout, stderr = local[exe][args].run(retcode=None)

            if ret == 0:
                conflicts = count_conflicts(outfile)
                if not writer:
                    print('%s: ' % scenario, end='')
                    if conflicts > 0:
                        print(colors.cyan | ('OK (%d conflicts)' % conflicts))
                    else:
                        print(colors.green | 'OK')
                else:
                    writer.writerow([project, mergecommit, left, right, file, strategy,
                                     conflicts])
            else:
                fail = True
                print('%s: ' % scenario, end='', file=sys.stderr)
                print(colors.red | ('FAILED (%d)' % ret), file=sys.stderr)
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
    parser.add_argument('-c', '--csv',
                        help='Print in csv format',
                        action="store_true")
    parser.add_argument('-n', '--noop',
                        help='Do not actually run',
                        action="store_true")
    parser.add_argument('commits', default=[], nargs='+')
    args = parser.parse_args()

    writer = None
    if args.csv:
        writer = csv.writer(sys.stdout, delimiter=';')

    if args.output:
        target = args.output
    else:
        target = tempfile.mkdtemp(prefix="jdime.")

    commits = args.commits

    if len(commits) == 1 and commits[0] == 'all':
        for commit in get_merge_commits():
            for job in get_jobs(target, args.noop, [commit,]):
                run(job, args.prune, writer, args.file, args.noop)
    else:
        for job in get_jobs(target, args.noop, commits):
            run(job, args.prune, writer, args.file, args.noop)

    if args.prune and not os.listdir(target):
        os.rmdir(target)
    elif not args.csv:
        print()
        if args.prune:
            stored = 'Erroneous'
        else:
            stored = 'All'
        print('%s merge scenarios have been stored to %s' % (stored, target))

if __name__ == "__main__":
    main()
