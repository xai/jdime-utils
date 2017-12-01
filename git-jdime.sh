#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -u

TMPLOG=$(mktemp)
: "${OUTPUT=/tmp/tmp.jdime.$(date +%Y%m%d%H%M%S)}"
: "${LOG:=${OUTPUT}/error.log}"

while read cmd; do
	echo $cmd
	$cmd > $TMPLOG 2>&1
	ret=$?
	if [ "$ret" != "0" ]; then
		(printf '=%.0s' {1..80}; echo "") >> $LOG
		date >> $LOG
		echo "$cmd" >> $LOG
		(printf -- '-%.0s' {1..80}; echo "") >> $LOG
		cat $TMPLOG >> $LOG
		(printf -- '-%.0s' {1..80}; echo "") >> $LOG
		echo "Failed with ${ret}." | tee -a $LOG
		echo >> $LOG
	fi
	rm "$TMPLOG"
done < <(git preparemerge -o $OUTPUT $@)
