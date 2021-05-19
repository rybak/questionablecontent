#!/bin/sh

# Starts QC wiki bot script 'qc_titles.py' in automatic mode.
# Useful for running the bot via crontab or similar scheduling utility.

$(dirname $0)/run.sh -auto 2>>/tmp/qc_titles.py.log
