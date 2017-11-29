#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -eu

while read cmd; do
	echo $cmd
	$cmd || echo "Failed with $?."
done < <(git preparemerge -o /tmp/tmp.jdime $@)
