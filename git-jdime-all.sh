#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -u

export OUTPUT=/tmp/tmp.jdime.$(date +%Y%m%d%H%M%S)
export LOG=${OUTPUT}/error.log

for commit in $(git rev-list --all --merges); do
	git jdime $commit
done