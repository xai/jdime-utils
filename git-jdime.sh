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

for strategy in linebased structured; do
    out=${target}/${strategy}
    jdimeargs="-eoe -m $strategy -r -q -o ${out}"
    trap "echo $target; exit $?" INT TERM EXIT
    jdime ${jdimeargs} ${target}/{left,base,right}
    trap - INT TERM EXIT
done

echo "$target"