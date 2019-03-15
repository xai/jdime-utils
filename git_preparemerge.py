#!/usr/bin/env python3
#
# Copyright (C) 2017 Olaf Lessenich

import argparse
import collections
import csv
import os
import sys
import tempfile
from plumbum import local
from plumbum.commands.processes import ProcessExecutionError

STRATEGY = '$$STRATEGY$$'
GIT = local['git']

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def get_merged_files(revs):
    merged_files = GIT['diff', '--name-status', '--diff-filter=M',
                       revs['left'], revs['right']]().splitlines()
    return map(lambda x: x[2:], merged_files)

def prepare_job(target, revs, file):
    path = os.path.dirname(file)

    for rev in STRATEGIES:
        os.makedirs(os.path.join(target, rev, path), exist_ok=True)

    for rev, commit in revs.items():
        if rev == 'merge':
            continue

        os.makedirs(os.path.join(target, rev, path), exist_ok=True)
        try:
            with open(os.path.join(target, rev, file), 'w') as targetfile:
                targetfile.write(GIT['show', commit + ":" + file]())
        except ProcessExecutionError:
            os.remove(os.path.join(target, rev, file))

def write_job(writer, target, project, timestamp, revs, file):
    inputfiles = []
    for rev in revs.keys():
        if rev == 'merge':
            continue

        inputfile = os.path.join(target, rev, file)
        if rev != 'base' or os.path.exists(inputfile):
            inputfiles.append(inputfile)
    outfile = os.path.join(target, STRATEGY, file)
    cmd = 'jdime -eoe -log WARNING -m %s -o %s %s' % (STRATEGY,
                                                      outfile,
                                                      ' '.join(inputfiles))
    writer.writerow([project, timestamp, revs['merge'], revs['left'], revs['right'],
                     file, ','.join(STRATEGIES), target, cmd])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('-m', '--modes',
                        help='Strategies to be prepared, separated by comma',
                        type=str,
                        default='structured')
    parser.add_argument('-n', '--noop',
                        help='Do not actually run',
                        action="store_true")
    parser.add_argument('-s', '--statedir',
                        help='Use state files to skip completed tasks',
                        type=str)
    parser.add_argument('commits', default=[], nargs='+')
    args = parser.parse_args()

    global STRATEGIES

    if args.output:
        target = args.output
    else:
        target = tempfile.mkdtemp(prefix="jdime.")

    project = os.path.basename(os.getcwd())
    revs = collections.OrderedDict()
    commits = args.commits

    if args.modes:
        STRATEGIES = args.modes.split(',')

    state=None
    if args.statedir:
        statedir = args.statedir
        if not os.path.exists(statedir):
            os.makedirs(statedir)
        state = os.path.join(statedir, project)

    if len(commits) is 1:
        # Only mergecommit is specified. We need to compute left and right.
        mergecommit = GIT['rev-parse', commits[0]]().strip()
        try:
            left, right = GIT['log', '--pretty=%P', '-n1',
                              mergecommit]().strip().split(' ')
        except ValueError:
            # octopus are merges not supported by us
            sys.exit(0)
        target = os.path.join(target, commits[0])
    else:
        # Left and right are provided. Need to find merge commit.
        # TODO: it would be really great if this was easier
        left = GIT['rev-parse', commits[0]]().strip()
        right = GIT['rev-parse', commits[1]]().strip()
        mergecommit = None
        for line in GIT['log', '--pretty=%H %P', '--all']().splitlines():
            scenario = line.strip().split(' ')
            if len(scenario) != 3:
                continue
            if scenario[1] == left and scenario[2] == right:
                mergecommit = scenario[0]
                break
        assert mergecommit is not None
        target = os.path.join(target, commits[0] + '-' + commits[1])

    if os.path.exists(target):
        eprint('Error! Directory exists: %s\nExiting.' % target)
        sys.exit(1)

    if state and os.path.isfile(state):
        with open(state, 'r') as f:
            for task in csv.DictReader(f, delimiter=';', fieldnames=['project',
                                                                     'merge',
                                                                     'strategy']):
                if task['merge'] == mergecommit:
                    if task['strategy'] in STRATEGIES:
                        STRATEGIES.remove(task['strategy'])

    if len(STRATEGIES) == 0:
        return

    revs['merge'] = mergecommit
    revs['left'] = left
    try:
        revs['base'] = GIT['merge-base', left, right]().strip()
    except ProcessExecutionError:
        # two-way merge
        pass
    revs['right'] = right

    timestamp = GIT['log', '--pretty=%ci', '-n1', mergecommit]().strip()

    writer = csv.writer(sys.stdout, delimiter=';')
    for file in get_merged_files(revs):
        if file.endswith('.java'):
            if not args.noop:
                prepare_job(target, revs, file)
            write_job(writer, target, project, timestamp, revs, file)

if __name__ == "__main__":
    main()
