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

strategies="linebased structured"
for strategy in $strategies; do
	mkdir -p ${target}/${strategy}
done

base=$(git merge-base $left $right)

merged=$(git diff --name-status --diff-filter=M $left $right | awk '{ print $2 }')
#added=$(git diff --name-status --diff-filter=A $left $right | awk '{ print $2 }')
#deleted=$(git diff --name-status --diff-filter=D $left $right | awk '{ print $2 }')

run=${RUN:-false}
jdimeargs="-eoe -q"
cmdfile=${target}/run.sh

for f in $merged; do
	path=$(dirname $f)
	filename=$(basename $f)
	mkdir -p ${target}/{left,base,right}/${path}
	lfile=${target}/left/${path}/${filename}
	bfile=${target}/base/${path}/${filename}
	rfile=${target}/right/${path}/${filename}
	git show ${base}:$f > $bfile || touch $bfile
	git show ${left}:$f > $lfile
	git show ${right}:$f > $rfile

	if $run; then
		for strategy in $strategies; do
			outfile=${target}/${strategy}/${path}/${filename}
			mkdir -p $(dirname $outfile)
			echo "jdime -m ${strategy} ${jdimeargs} -o ${outfile} ${lfile} ${bfile} ${rfile}" >> ${cmdfile}
		done
	fi

done

if not $run; then
	for strategy in $strategies; do
		out=${target}/${strategy}
		echo jdime -m ${strategy} ${jdimeargs} -r -o ${target}/${strategy} ${target}/{left,base,right} >> ${cmdfile}
	done
fi

echo "${target}"
