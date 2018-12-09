#!/bin/sh
CSV="$HOME/csv"

cd $CSV
echo "Project;Files;Conflicting Files;Conflicts"
for csv in *.csv; do
	awk -F';' 'BEGIN { rows=0; crows=0; conflicts=0 } { repo=$1; rows++; if($6!=0) { crows++; conflicts+=$6 } } END { print repo";"rows";"crows";"conflicts }' $csv
done
