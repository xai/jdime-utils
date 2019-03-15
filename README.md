# jdime-utils
A collection of utilities and small scripts around JDime

# Requirements
* [plumbum](https://plumbum.readthedocs.io/en/latest/): `pip3 install --user plumbum`
* git
* curl
* [jdime](https://github.com/xai/jdime) (preferrably develop branch)

# Install
Assuming that `$HOME/bin` is in your `$PATH`:  
`ln -s $(readlink -f git_preparemerge.py) $HOME/bin/git-preparemerge`  
`ln -s $(readlink -f git_jdime.py) $HOME/bin/git-jdime`  

Please ensure that `jdime` is in your `$PATH` as well.  
My personal way to install jdime is this:
```
git clone https://github.com/xai/jdime
git clone https://gitlab.infosun.fim.uni-passau.de/seibt/JNativeMerge
cd jdime
git checkout develop
mkdir $HOME/opt
make install
echo "#!/bin/sh" > $HOME/bin/jdime
echo "$HOME/opt/JDime/bin/JDime $@" >> $HOME/bin/jdime
chmod +x $HOME/bin/jdime
```

# Config
To specify which strategies should be used, edit the respective list
in the config section at the beginning of `git_preparemerge.py`.

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
usage: git-jdime [-h] [-o OUTPUT] [-f FILE] [-p] commit(s)/all

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Store output in this directory
  -f FILE, --file FILE  Merge only specified file
  -p, --prune           Prune successfully merged scenarios
  -c, --csv             Print in csv format
  ```
