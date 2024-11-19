#!/bin/sh

# This is the Python command required to run the QC wiki bot script
# 'qc_titles.py'.  For available options, see file 'bot/qc_titles.py'.

# the configuration file shall provide $BOT_LOCATION
. $(dirname $0)/bot/config.sh
cd "$(dirname $0)/bot/$BOT_LOCATION"
python pwb.py login
exec python pwb.py qc_titles "${@}"
