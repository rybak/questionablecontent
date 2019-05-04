#!/bin/bash

#
# Script to download all comic views from http://questionablecontent.net/
#

LAST=3995

START=$(date)
echo "Started: $START"

for i in $(seq 1 $LAST)
do
	DIR=$(printf "%02d" $(( $i / 100 )))
	z=$(printf "%04d" $i)
	echo "$DIR / $z ($i)"
	mkdir -p "$DIR"

	file="$DIR/$z.html"
	wget "http://www.questionablecontent.net/view.php?comic=$i" -O "$file"

	sleep $(( $RANDOM % 5 ))
done

echo "Started : $START"
echo "Finished: $(date)"
