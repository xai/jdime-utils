#!/bin/bash
PROJECTS="$HOME/projects"
REPOS="$HOME/repos"
CSV="$HOME/csv"
TMPDIR="/tmp/jdime"

SCRIPTS="$(dirname $(realpath $0))"

for url in $(cat $PROJECTS); do
	cd $REPOS
	repo=$(echo "$url" | cut -d'/' -f5)
	if [ ! -d ${repo}/.git ]; then
		header=$(curl -sI $url)
		while ( echo "$header" | egrep -q '^Status: 301 ' ); do
			url=$(echo "$header" | egrep '^Location: ' | awk -F': ' '{ print $2 }')
			header=$(curl -sI $url)
		done
		if ( echo "$header" | egrep -q '^Status: 200 OK' ); then
			git clone -q $url $repo
		fi
	fi
	if [ -d ${repo} ]; then
		cd ${repo}
		git jdime -o $TMPDIR -p all -c | tee ${CSV}/${repo}.csv | ${SCRIPTS}/colorize.py
	fi
done
