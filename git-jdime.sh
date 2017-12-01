#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -u

TMPLOG=$(mktemp)
: "${OUTPUT=/tmp/tmp.jdime.$(date +%Y%m%d%H%M%S)}"
: "${LOG:=${OUTPUT}/error.log}"

while IFS=';' read project left right file strategy cmd; do
	left=$(echo "$left" | cut -c1-7)
	right=$(echo "$right" | cut -c1-7)
	echo -n "$project $left $right $file $strategy"
	$cmd > $TMPLOG 2>&1
	ret=$?
	if [ "$ret" != "0" ]; then
		echo ": $(tput setaf 1)FAILED (${ret})$(tput sgr 0)"
		(printf '=%.0s' {1..80}; echo "") >> $LOG
		date >> $LOG
		echo "$project $left $right $file $strategy" >> $LOG
		echo "> $cmd" >> $LOG
		(printf -- '-%.0s' {1..80}; echo "") >> $LOG
		cat $TMPLOG >> $LOG
		(printf -- '-%.0s' {1..80}; echo "") >> $LOG
		echo "Failed with ${ret}." >> $LOG
		echo >> $LOG
	else
		echo ": $(tput setaf 2)OK$(tput sgr 0)"
	fi
	rm "$TMPLOG"
done < <(git preparemerge -o $OUTPUT $@)
