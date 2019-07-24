# jdime-utils
A collection of utilities and small scripts around JDime

# Requirements
* python3
* pip3
* [plumbum](https://plumbum.readthedocs.io/en/latest/): `pip3 install --user plumbum`
* psutil: `pip3 install --user psutil`
* git
* curl
* [jdime](https://github.com/xai/jdime) (preferrably benchmark branch)

# Install
Assuming that `$HOME/bin` is in your `$PATH`:  
`ln -s $(readlink -f git_preparemerge.py) $HOME/bin/git-preparemerge`  
`ln -s $(readlink -f git_jdime.py) $HOME/bin/git-jdime`  

Please ensure that `jdime` is in your `$PATH` as well.

My personal way to install jdime for benchmarking is this:
```
git clone https://github.com/xai/jdime
cd jdime
git checkout benchmark
mkdir $HOME/opt
make install
echo '#!/bin/sh' > $HOME/bin/jdime
echo '$HOME/opt/JDime/bin/JDime $@' >> $HOME/bin/jdime
chmod +x $HOME/bin/jdime
```

If I plan on hacking JDime itself, it's easier this way (skipping deployment to ~/opt):
```
git clone https://github.com/xai/jdime
cd jdime
git checkout benchmark
./gradlew installDist
ln -s /path/to/jdime/build/install/JDime/bin/JDime $HOME/bin/jdime
```

# Config
To specify which strategies should be used, use the `-m` switches of 
`git preparemerge` and `git jdime`.  
Multiple strategies are provided as a comma separated list, e.g., `-m linebased,structured`.
Combined strategies (auto-tuning) are provided with a '+', .e.g., `-m linebased+structured`.

# Use
To run jdime with these scripts on merge commits of a git repository, 
`cd` into the workdir of the repository.

To run jdime on a specific merge commit, run  
`git jdime <hash-of-mergecommit>` or  
`git jdime <hash-of-left-parent> <hash-of-right-parent>`

To run jdime on all merge commits, run  
`git jdime all`

You can also use command line arguments to specify the output directory,
keep only merge scenarios in which jdime breaks (error or exception),
or execute a merge only for a specific file:  
```
usage: git-jdime [-h] [-o OUTPUT] [-m MODES] [-j JDIMEOPTS] [-f FILE] [-p]
                 [-c] [-H] [-n] [-s STATEDIR] [-b BEFORE] [-r RUNS] [-t TAG]
                 commits [commits ...]

positional arguments:
  commits

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Store output in this directory
  -m MODES, --modes MODES
                        Strategies to be prepared, separated by comma
  -j JDIMEOPTS, --jdimeopts JDIMEOPTS
                        Additional options to pass to jdime
  -f FILE, --file FILE  Merge only specified file
  -p, --prune           Prune successfully merged scenarios
  -c, --csv             Print in csv format
  -H, --header          Include csv header
  -n, --noop            Do not actually run
  -s STATEDIR, --statedir STATEDIR
                        Use state files to skip completed tasks
  -b BEFORE, --before BEFORE
                        Use only commits before <date>
  -r RUNS, --runs RUNS  Run task this many times (e.g., for benchmarks)
  -t TAG, --tag TAG     Append this tag to each line
  ```

While `-c` is optional for now, it probably will be default in future versions, as I always use it anyway.  
To have better human readable output, pipe the csv output to `scripts/colorize.py`.  
I typically use `-t` to add information on my test environment, like the commit hash of jdime/jdime-utils and the hostname of the machine I'm using. This makes it easier to sort csvs later.  

# Example
A practical example looks like this:  
```
cd ~/repos/someproject
git jdime -o /tmp/jdime -p -H -c -m linebased,structured,linebased+structured all | tee ~/csvs/someproject.csv | ~/path/to/jdime-utils/scripts/colorize.py
```
This runs the strategies linebased, structured, and a combined strategy on all merge commits of the project, stores a ';'-separated csv file to ~/csvs/someproject.csv, and provides colored, human readable output on stdout. The files that are being merged and the respective merge output is written to a temporary directory named /tmp/jdime. All scenarios that did not fail are deleted from that directory after a run. The ones that failed will be preserved, the reason for the failure is written to a respective error.log in that directory.
