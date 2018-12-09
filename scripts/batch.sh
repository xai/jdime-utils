#!/bin/bash
PROJECTS="$HOME/projects"
REPOS="$HOME/repos"
CSV="$HOME/csv"
TMPDIR="/tmp/jdime"

for url in $(cat $PROJECTS); do
	cd $REPOS
	repo=$(echo "$url" | cut -d'/' -f5)
	if [ ! -d ${repo}/.git ]; then
		git clone -q $url || continue
	fi
	cd ${repo} || continue
	git jdime -o $TMPDIR -p all -c | tee ${CSV}/${repo}.csv
done
