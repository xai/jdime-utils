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
    merged_files = []
    skipped_files = {}
    modified_lr = GIT['diff', '--name-status', '--diff-filter=AM',
                   revs['left'] + '...' + revs['right']]().splitlines()
    modified_rl = GIT['diff', '--name-status', '--diff-filter=AM',
                   revs['right'] + '...' + revs['left']]().splitlines()
    left_files = set()
    right_files = set()
    left_files_new = set()
    right_files_new = set()
    for line in modified_lr:
        t, f = line.split('\t')[0:2]
        left_files.add(f)
        if t == 'A':
            left_files_new.add(f)
    for line in modified_rl:
        t, f = line.split('\t')[0:2]
        right_files.add(f)
        if t == 'A':
            right_files_new.add(f)

    renamed_lr = GIT['diff', '--name-status', '--diff-filter=R',
                       revs['left'] + '...' + revs['right']]().splitlines()
    renamed_rl = GIT['diff', '--name-status', '--diff-filter=R',
                       revs['right'] + '...' + revs['left']]().splitlines()
    left_renamed = {}
    right_renamed = {}
    for line in renamed_lr:
        old, new = line.split('\t')[1:3]
        left_renamed[new] = old
        left_files.add(new)
    for line in renamed_rl:
        old, new = line.split('\t')[1:3]
        right_renamed[new] = old
        right_files.add(new)

    intersection = left_files.intersection(right_files)
    for f in intersection:
        if not f.endswith('.java'):
            skipped_files[f] = "non-java file"
            continue

        b = None
        if f in left_renamed:
            b = left_renamed[f]
        if f in right_renamed:
            if not b:
                b = right_renamed[f]
            else:
                if b != right_renamed[f]:
                    eprint("%s %s %s is a rename/rename conflict" %
                           (revs["left"], revs["right"], f))
                    skipped_files[f] = "rename/rename conflict"
                    continue

        if f in left_files_new or f in right_files_new:
            if b:
                # conflict on file level
                eprint("%s %s %s is a add/rename conflict" %
                       (revs["left"], revs["right"], f))
                skipped_files[f] = "add/rename conflict"
                continue
        elif not b:
            b = f

        if not b:
            eprint("%s %s %s is a two-way merge" %
                   (revs["left"], revs["right"], f))

        merged_files.append((f,b,f))

    for f in left_files.union(right_files).union(left_renamed.keys() |
                                                 set()).union(right_renamed.keys()
                                                             | set()):
        if f not in intersection:
            skipped_files[f] = "fast-forward"
            if not f.endswith('.java'):
                skipped_files[f] += " + non-java file"

    return (merged_files, skipped_files)

def prepare_job(target, revs, lbr, noop=False):
    l, b, r = lbr
    lpath = os.path.dirname(l)

    if not noop:
        for rev in STRATEGIES:
            os.makedirs(os.path.join(target, rev, lpath), exist_ok=True)

    keys = ("left", "base", "right")
    inputfiles = []
    for key, commit, filename in zip(keys, [ revs[key] if key in revs else None for key in keys ], lbr):

        if commit and filename:
            inputfile = os.path.join(target, key, filename)
            if not noop:
                os.makedirs(os.path.dirname(inputfile), exist_ok=True)
                try:
                    with open(inputfile, 'w') as targetfile:
                        targetfile.write(GIT['show', commit + ":" + filename]())
                except ProcessExecutionError:
                    os.remove(inputfile)

            inputfiles.append(inputfile)

    # return (inputfiles, os.path.join(target, STRATEGY, l))
    return (inputfiles, l)

def write_job(writer, target, project, timestamp, revs, jdimeopts, inputfiles, outputfile, reason=None):

    if len(inputfiles) > 0:
        mergetype = ("%d-way" % len(inputfiles))
        outfile = os.path.join(target, STRATEGY, outputfile)

        if jdimeopts:
            jdimeopts = '-' + jdimeopts
        else:
            jdimeopts = ''

        cmd = 'jdime -eoe -log WARNING -s -m %s -o %s %s %s' % (STRATEGY,
                                                                outfile,
                                                                jdimeopts,
                                                                ' '.join(inputfiles))
        strategies = ','.join(STRATEGIES)
    else:
        mergetype = "skipped"
        cmd = reason
        target = ""
        strategies = ""

    writer.writerow([project, timestamp, revs['merge'], revs['left'], revs['right'],
                     outputfile, mergetype, strategies, target, cmd])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('-m', '--modes',
                        help='Strategies to be prepared, separated by comma',
                        type=str,
                        default='structured')
    parser.add_argument('-j', '--jdimeopts',
                        help='Additional options to pass to jdime',
                        type=str)
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
        if revs['base'] == left or revs['base'] == right:
            eprint("%s is a fast-forward merge" % mergecommit)
            # return
    except ProcessExecutionError:
        # two-way merge
        eprint("%s is a two-way merge" % mergecommit)
        pass
    revs['right'] = right

    timestamp = GIT['log', '--pretty=%ci', '-n1', mergecommit]().strip()

    writer = csv.writer(sys.stdout, delimiter=';')
    merged_files, skipped_files = get_merged_files(revs)
    for lbr in merged_files:
        inputfiles, outputfile = prepare_job(target, revs, lbr, args.noop)
        write_job(writer, target, project, timestamp, revs, args.jdimeopts,
                  inputfiles, outputfile)
    for f, reason in skipped_files.items():
        write_job(writer, target, project, timestamp, revs, args.jdimeopts,
                  [], f, reason)

if __name__ == "__main__":
    main()
