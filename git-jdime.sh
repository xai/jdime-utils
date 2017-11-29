#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -eu

if [ "$#" -lt 2 ]; then
	IFS=" " read left right <<< $(git log --pretty=%P -n1 $1)
else
	left="$1"
	right="$2"
fi

trap "echo Something went wrong; exit $?" INT TERM EXIT
target=$(git preparemerge $left $right /tmp/tmp.jdime)
trap - INT TERM EXIT

errlog=${target}/$$.err
out=${target}/out

while read cmd; do
	echo $cmd
	if not $cmd > $out 2>&1; then
		date >> $errlog
		echo $cmd >> $errlog
		cat $out | tee -a $errlog
		echo >> $errlog
	fi
done < ${target}/run.sh

echo "$target"
