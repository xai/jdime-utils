#!/bin/bash
#
# Copyright (C) 2017 Olaf Lessenich
#

set -eu

left="$1"
right="$2"

target=${3:-""}
if [ -z "$target" ]; then
    target=$(mktemp -d)
elif [ -d $target ]; then
    echo "$target already exists! Exiting."; exit 1
fi
mkdir -p ${target}/{left,base,right}

base=$(git merge-base $left $right)

merged=$(git diff --name-status --diff-filter=M $left $right | awk '{ print $2 }')
#added=$(git diff --name-status --diff-filter=A $left $right | awk '{ print $2 }')
#deleted=$(git diff --name-status --diff-filter=D $left $right | awk '{ print $2 }')

for f in $merged; do
    path=$(dirname $f)
    filename=$(basename $f)
    mkdir -p ${target}/{left,base,right}/${path}
    git show ${base}:$f > ${target}/base/${path}/${filename} || touch ${target}/base/${path}/${filename}
    git show ${left}:$f > ${target}/left/${path}/${filename}
    git show ${right}:$f > ${target}/right/${path}/${filename}
done

echo "${target}"