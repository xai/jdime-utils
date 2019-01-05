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


###############################################################################
# <CONFIG>

# example: STRATEGIES = ['linebased', 'structured']
STRATEGIES = ['linebased']

# </CONFIG>
###############################################################################

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
        os.makedirs(os.path.join(target, rev, path), exist_ok=True)
        try:
            with open(os.path.join(target, rev, file), 'w') as targetfile:
                targetfile.write(GIT['show', commit + ":" + file]())
        except ProcessExecutionError:
            os.remove(os.path.join(target, rev, file))

def write_job(writer, target, project, revs, file):
    inputfiles = []
    for rev in revs.keys():
        inputfile = os.path.join(target, rev, file)
        if rev != 'base' or os.path.exists(inputfile):
            inputfiles.append(inputfile)
    outfile = os.path.join(target, STRATEGY, file)
    cmd = 'jdime -eoe -log WARNING -m %s -o %s %s' % (STRATEGY,
                                                      outfile,
                                                      ' '.join(inputfiles))
    writer.writerow([project, revs['left'], revs['right'],
                     file, ','.join(STRATEGIES), target, cmd])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('commits', default=[], nargs='+')
    args = parser.parse_args()

    if args.output:
        target = args.output
    else:
        target = tempfile.mkdtemp(prefix="jdime.")

    project = os.path.basename(os.getcwd())
    revs = collections.OrderedDict()
    commits = args.commits

    if len(commits) is 1:
        # Only mergecommit is specified. We need to compute left and right.
        try:
            left, right = GIT['log', '--pretty=%P', '-n1',
                              commits[0]]().strip().split(' ')
        except ValueError:
            # octopus are merges not supported by us
            sys.exit(0)
        target = os.path.join(target, commits[0])
    else:
        # Left and right are provided.
        left = commits[0]
        right = commits[1]
        target = os.path.join(target, commits[0] + '-' + commits[1])

    if os.path.exists(target):
        eprint('Error! Directory exists: %s\nExiting.' % target)
        sys.exit(1)
    
    revs['left'] = left
    try:
        revs['base'] = GIT['merge-base', left, right]().strip()
    except ProcessExecutionError:
        # two-way merge
        pass
    revs['right'] = right

    writer = csv.writer(sys.stdout, delimiter=';')
    for file in get_merged_files(revs):
        if file.endswith('.java'):
            prepare_job(target, revs, file)
            write_job(writer, target, project, revs, file)

if __name__ == "__main__":
    main()
