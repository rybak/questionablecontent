#!/bin/bash

source config.sh

set -u
filename='qc_titles.py'
DEST="${BOT_LOCATION}/scripts/userscripts"
SRC="."

source overwrite.sh

ls -l "$DEST"
