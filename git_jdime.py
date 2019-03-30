#!/usr/bin/env python3
#
# Copyright (C) 2017 Olaf Lessenich

import argparse
import csv
import os
import sys
import tempfile
import time
import statistics
from plumbum import colors
from plumbum import local
from plumbum.cmd import grep
from plumbum.commands.processes import ProcessExecutionError
from xml.etree import ElementTree as ET


GIT = local['git']
STRATEGY = '$$STRATEGY$$'
COLS = ['project', 'timestamp', 'merge', 'left', 'right', 'file', 'mergetype',
        'strategies', 'target', 'cmd']

def get_merge_commits(before):
    if before:
        return GIT['rev-list', '--all', '--merges', '--reverse',
                   '--before', before]().splitlines()
    else:
        return GIT['rev-list', '--all', '--merges', '--reverse']().splitlines()

def get_jobs(target, strategies=None, jdimeopts=None, noop=False, statedir=None, commits=[]):
    options = ["-o", target]
    if strategies:
        options.append("-m")
        options.append(','.join(strategies))
    if noop:
        options.append("-n")
    if jdimeopts:
        options.append("-j")
        options.append(jdimeopts)
    if statedir:
        options.append("-s")
        options.append(statedir)
    return csv.DictReader(iter(GIT['preparemerge', options, commits]()\
                               .splitlines()), delimiter=';', fieldnames=COLS)

def count_conflicts(merged_file):
    conflicts = 0

    try:
        m1 = int(grep['-c', '-e', '^<<<<<<<', merged_file]().strip())
        m2 = int(grep['-c', '-e', '^=======', merged_file]().strip())
        m3 = int(grep['-c', '-e', '^>>>>>>>', merged_file]().strip())
        conflicts = min(m1, m2, m3)
    except ProcessExecutionError:
        pass

    return conflicts

def run(job, prune, writer, runs=1, srcfile=None, noop=False):

    if noop:
        writer = csv.DictWriter(sys.stdout, delimiter=';', fieldnames=COLS)
        writer.writerow(job)
        return

    project = job['project']
    timestamp = job['timestamp']
    mergecommit = job['merge'][0:7]
    left = job['left'][0:7]
    right = job['right'][0:7]
    file = job['file']
    target = job['target']
    mergetype = job['mergetype']

    fail = False

    if mergetype == "skipped":
        writer.writerow([project,
                         timestamp,
                         mergecommit,
                         left,
                         right,
                         file,
                         mergetype,
                         job["cmd"],
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         '',
                         jdimeversion])
        return


    if not srcfile or srcfile == file:
        errorlog = os.path.join(target, 'error.log')
        strategies = job['strategies'].split(',')
        for strategy in strategies:
            strategy = strategy.replace('+', ',')
            scenario = '%s %s %s %s %s %s %s %s' % (project, timestamp,
                                                    mergecommit, left, right,
                                                    file, mergetype, strategy)
            cmd = job['cmd'].replace(STRATEGY, strategy).split(' ')
            exe = cmd[0]
            args = cmd[1:]
            outfile = args[7]

            runtimes = []
            for i in range(runs):
                if os.path.exists(outfile):
                    os.remove(outfile)
                t0 = time.time()
                ret, stdout, stderr = local[exe][args].run(retcode=None)
                t1 = time.time()
                runtimes.append(t1 - t0)
            runtime = statistics.median(runtimes)

            if ret >= 0 and ret <= 127:
                tree = ET.fromstring(stdout)
                conflicts = int(tree.find("./mergescenariostatistics/conflicts").text)
                clines = int(tree.find('./mergescenariostatistics/lineStatistics').attrib['numOccurInConflict'])
                ctokens = int(tree.find('./mergescenariostatistics/tokenStatistics').attrib['numOccurInConflict'])
                parsed_conflicts = count_conflicts(outfile)
                xmlruntimes={'merge': None,
                             'parse': None,
                             'semistructure': None,
                             'LinebasedStrategy': None,
                             'SemiStructuredStrategy': None,
                             'StructuredStrategy': None}

                for e in tree.findall("./mergescenariostatistics/runtime"):
                    for label in xmlruntimes:
                        if label == e.attrib['label']:
                            xmlruntimes[label] = int(e.attrib['timeMS'])

                if not writer:
                    print('%s: ' % scenario, end='')
                    if conflicts > 0:
                        print(colors.cyan | ('OK (%d conflicts)' % conflicts))
                    else:
                        print(colors.green | 'OK')
                else:
                    writer.writerow([project,
                                     timestamp,
                                     mergecommit,
                                     left,
                                     right,
                                     file,
                                     mergetype,
                                     strategy,
                                     conflicts,
                                     clines,
                                     ctokens,
                                     parsed_conflicts,
                                     runtime,
                                     xmlruntimes['merge'],
                                     xmlruntimes['parse'],
                                     xmlruntimes['semistructure'],
                                     xmlruntimes['LinebasedStrategy'],
                                     xmlruntimes['SemiStructuredStrategy'],
                                     xmlruntimes['StructuredStrategy'],
                                     jdimeversion])
            else:
                fail = True
                if not writer:
                    print('%s: ' % scenario, end='', file=sys.stderr)
                    print(colors.red | ('FAILED (%d)' % ret), file=sys.stderr)
                else:
                    writer.writerow([project,
                                     timestamp,
                                     mergecommit,
                                     left,
                                     right,
                                     file,
                                     'FAILED (' + str(ret) + ')',
                                     strategy,
                                     '',
                                     '',
                                     '',
                                     '',
                                     runtime,
                                     '',
                                     '',
                                     '',
                                     '',
                                     '',
                                     '',
                                     jdimeversion])
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

def write_state(project, commit, strategies, statedir):
    if statedir:
        statefile = os.path.join(statedir, project)
        if os.path.exists(statefile):
            with open(statefile, 'r') as f:
                for done in csv.DictReader(f, delimiter=';', fieldnames=['project',
                                                                         'commit',
                                                                         'strategy']):
                    if project == done['project'] and commit == done['commit']:
                        if done['strategy'] in strategies:
                            strategies.remove(done['strategy'])
                            if len(strategies) == 0:
                                return


        with open(statefile, 'a') as f:
            statewriter = csv.writer(f, delimiter=';')
            for strategy in strategies:
                statewriter.writerow([project,
                                      commit,
                                      strategy])

def main():
    global jdimeversion
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='Store output in this directory',
                        type=str)
    parser.add_argument('-m', '--modes',
                        help='Strategies to be prepared, separated by comma',
                        type=str,
                        default='structured,linebased')
    parser.add_argument('-j', '--jdimeopts',
                        help='Additional options to pass to jdime',
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
    parser.add_argument('-H', '--header',
                        help='Include csv header',
                        action="store_true")
    parser.add_argument('-n', '--noop',
                        help='Do not actually run',
                        action="store_true")
    parser.add_argument('-s', '--statedir',
                        help='Use state files to skip completed tasks',
                        type=str)
    parser.add_argument('-b', '--before',
                        help='Use only commits before <date>',
                        type=str)
    parser.add_argument('-r', '--runs',
                        help='Run task this many times (e.g., for benchmarks)',
                        type=int,
                        default=1)
    parser.add_argument('-t', '--tag',
                        help='Append this tag to each line',
                        type=str)
    parser.add_argument('commits', default=[], nargs='+')
    args = parser.parse_args()

    strategies = args.modes.split(',')

    writer = None
    if args.csv:
        writer = csv.writer(sys.stdout, delimiter=';')
        if args.header:
            outputcols = ['project',
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
            writer.writerow(outputcols)
    if args.output:
        target = args.output
    else:
        target = tempfile.mkdtemp(prefix="jdime.")

    if args.statedir:
        if not os.path.exists(args.statedir):
            os.makedirs(args.statedir)

    if args.tag:
        jdimeversion = args.tag
    else:
        jdimeversion = local['jdime']['-v']().strip()
    if args.runs > 1:
        jdimeversion += " runs:" + str(args.runs)
    # make sure this doesn't interfere with our csv delimiter
    jdimeversion.replace(';', ',')

    project = os.path.basename(os.getcwd())
    commits = args.commits

    if len(commits) == 1 and commits[0] == 'all':
        for commit in get_merge_commits(args.before):
            for job in get_jobs(target, strategies, args.jdimeopts, args.noop, args.statedir, [commit,]):
                run(job, args.prune, writer, args.runs, args.file, args.noop)
            write_state(project, commit, strategies.copy(), args.statedir)
    else:
        for job in get_jobs(target, strategies, args.jdimeopts, args.noop, args.statedir, commits):
            run(job, args.prune, writer, args.runs, args.file, args.noop)
        for commit in commits:
            write_state(project, commit, strategies.copy(), args.statedir)

    if args.prune and os.path.exists(target) and not os.listdir(target):
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
