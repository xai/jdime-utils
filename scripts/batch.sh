#!/usr/bin/env bash
PROJECTS="$HOME/projects.txt"
REPOS="$HOME/repos"
CSV="$HOME/csv"
TMPDIR="/tmp/jdime"
STATEDIR="$HOME/state"
JDIMESRC="$HOME/src/jdime"

SCRIPTS="$(dirname $(readlink -f $0))"

workingdir=$(pwd)
cd $JDIMESRC || ( echo "$JDIMESRC not found"; exit 1 )
JDIMEVERSION="$(git rev-parse --short HEAD)"

OPTIONS=""
if [ -n "$1" ]; then
	OPTIONS="-b $1"
	shift
fi

if [ -n "$1" ]; then
	urls="$@"
else
	urls="$(cat $PROJECTS)"
fi

for url in $urls; do
	url=$(echo "$url" | sed -e 's/http:/https:/')
	cd $REPOS
	repo=$(echo "$url" | cut -d'/' -f5)
	if [ ! -d "${repo}/.git" ]; then
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
	if [ -d "${repo}" ]; then
		cd ${repo}
		git jdime -o $TMPDIR -s $STATEDIR -t $JDIMEVERSION -m linebased,structured,linebased+structured,linebased+semistructured+structured,semistructured -p $OPTIONS all -c -r 10 | tee -a ${CSV}/${repo}.csv | ${SCRIPTS}/colorize.py
	fi
done
