#!/usr/bin/env bash
PROJECTS="$HOME/projects"
REPOS="$HOME/repos"
CSV="$HOME/csv"
TMPDIR="/tmp/jdime"
STATEDIR="$HOME/state"

SCRIPTS="$(dirname $(readlink -f $0))"

OPTIONS=""
if [ -n $1 ]; then
	OPTIONS="-b $1"
fi

for url in $(cat $PROJECTS); do
	url=$(echo "$url" | sed -e 's/http:/https:/')
	cd $REPOS
	repo=$(echo "$url" | cut -d'/' -f5)
	if [ ! -d ${repo}/.git ]; then
		header=$(curl -sI $url)
		echo "Trying to fetch url: $url" 1>&2
		while ( echo "$header" | egrep -q '^Status: 301 ' ); do
			url="$(echo "$header" | egrep '^Location: ' | sed -e 's/Location: //' -e 's/\r//')"
			echo "Project has moved to new location: $url" 1>&2
			header=$(curl -sI $url)
		done
		if ( echo "$header" | egrep -q '^Status: 200 OK' ); then
			echo "git clone -q $url $repo" 1>&2
			git clone -q $url $repo
		fi
	fi
	if [ -d ${repo} ]; then
		cd ${repo}
		git jdime -o $TMPDIR -s $STATEDIR -m linebased,structured,linebased+structured -p $OPTIONS all -c | tee ${CSV}/${repo}.csv | ${SCRIPTS}/colorize.py
	fi
done
