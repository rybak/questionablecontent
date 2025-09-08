#!/bin/bash

#
# Script to download all comic views from http://questionablecontent.net/
#

LAST=${2:-$(grep -m 1 -o '[1-9][0-9]*' ../core_stable/data.lua | head -1 || echo "5000")}
let FROM=${1:-${LAST}-300}
echo "$FROM .. $LAST"

START=$(date)
echo "Started: $START"
root_url='https://www.questionablecontent.net'

for i in $(seq $FROM $LAST)
do
	DIR=$(printf "%02d" $(( $i / 100 )))
	z=$(printf "%04d" $i)
	echo -n "$DIR / $z ($i) - "
	mkdir -p "$DIR"

	file="$DIR/$z.html"
	file1="$i.png"
	file2="$i.gif"
	file3="$i.jpg"
	t1="$DIR/$z.png"
	t2="$DIR/$z.gif"
	t3="$DIR/$z.jpg"
	if [[ ! -s "$t1" ]] && [[ -f "$t1" ]]
	then
		rm "$t1" && echo -n "$t1 was empty - "
	fi
	if [[ ! -s "$t2" ]] && [[ -f "$t2" ]]
	then
		rm "$t2" && echo -n "$t2 was empty - "
	fi
	if [[ ! -s "$t3" ]] && [[ -f "$t3" ]]
	then
		rm "$t3" && echo -n "$t3 was empty - "
	fi
	if [[ -f "$t1" ]] || [[ -f "$t2" ]] || [[ -f "$t3" ]]
	then
		echo "OK"
	else
		echo "Downloading..."
		curl "$root_url/comics/$file1" -o "$t1" || \
			curl "$root_url/comics/$file2" -o "$t2" || \
			curl "$root_url/comics/$file3" -o "$t3"
		if [[ ! -s "$t1" ]] && [[ -f "$t1" ]]
		then
			rm "$t1" && echo -n "$t1 is empty - "
		fi
		if [[ ! -s "$t2" ]] && [[ -f "$t2" ]]
		then
			rm "$t2" && echo -n "$t2 is empty - "
		fi
		if [[ ! -s "$t3" ]] && [[ -f "$t3" ]]
		then
			rm "$t3" && echo -n "$t3 is empty - "
		fi
		ls -l "$DIR/$z"*
		sleep $(( $RANDOM % 5 ))
	fi
done

echo "Started : $START"
echo "Finished: $(date)"
