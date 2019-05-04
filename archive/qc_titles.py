#!/usr/bin/env python3

#
# qc_titles.py
#
# Andrei Rybak © 2019
# Written for Questionable Content Wiki
# https://questionablecontent.fandom.com
#
# This script parses HTML of https://questionablecontent.net/archive.php
# to generate Lua-syntax table with all the comic titles.
#
# Usage:
#
#   1. Save the HTML of the archive page. Either manually, or using curl:
#      $ curl -O https://questionablecontent.net/archive.php
#
#   2. Launch the script:
#      $ ./qc_titles.py archive.php data.lua
#
#   3. Copy the output from file 'data.lua' to the dataset page
#      https://questionablecontent.fandom.com/wiki/Module:QC/titles
#
# Script uses only standard Python 3 library and does not have external
# dependencies.
#

import sys
import re
from textwrap import dedent


def url(n):
    return 'https://www.questionablecontent.net/view.php?comic=' + str(n)


DEBUG=False
f = "archive.php"
output = "data.lua"
if len(sys.argv) > 1:
    f = sys.argv[1]
if len(sys.argv) > 2:
    output = sys.argv[2]

ls = []
with open(f, encoding='utf-8', errors='ignore') as tmp:
    ls = tmp.readlines()

print("Parsing '{}'...".format(f))
print("Number of lines: {}".format(len(ls)))
# parse every line to a list of tuples (<number>, <title>)
res = []
#  Regex to parse <a> tags:   group 1, number      group 2, title
#                                   _____|____               _|
#                                  /          \             /  \
p = re.compile('view\\.php\\?comic=([0-9]{1,4}).*Comic \\1: (.*)</a>')
non_letters = re.compile('[^a-zA-Z]*')
for line in ls:
    m = p.search(line)
    if not m:
        continue
    num = m.group(1)
    t = m.group(2)
    res.append((num, t))
    if DEBUG and non_letters.fullmatch(t):
        r = res[-1]
        print(r)
        print(url(num))
print("Got {} raw results.".format(len(res)))

if DEBUG:
    print(res[500])
    print(res[1500])
    print(res[2500])

# put from list to a dictionary to remove duplicates
m = {}  # dict from comic number to title
for r in res:
    if DEBUG and r[0] == '3911':
        print(r)
    m[int(r[0])] = r[1]

# check if any are missing
for n in range(1, max(m) + 1):
    if n not in m:
        print("Missing comic #{}".format(n))

### fix known issues of the archive.php page ###
## missing in archive.php
m[570] = "She Missed It All"
m[870] = "Semi-Naker!"

## missing titles
m[878] = "One Flew Over The Cuckoo's Nest"
m[2770] = "Plans Gone Awry" 

## broken titles
# misnumbered as 931
m[971] = "Clean Freak by supar-webcomorx guest artiste Ryan Estrada"
# completely overwritten by 3906 for some reason
m[3901] = "Multiple Anatomy"
# title duplicate overwritten by title from 2153
m[2155] = "Be More Obvious"
# title duplicate overwritten by title from 2393
m[2394] = "Greeting Gauntlet"
# comic 2308 is duplicated with a broken link to view.php?comic=0
del(m[0])

# HTML encode these two just in case
m[2680] = "&gt;:|"  # angry emoticon ">:|"
m[3911] = "&lt; body &gt;"  # body tag "< body >"

print("Got {} comic titles after cleanup.".format(len(m)))


def lua_item(r):
    # some titles have quotes in them
    return '[{}]="{}",'.format(r[0], r[1].replace('"', '\\"'))


# write out like a Lua table
with open(output, 'w', encoding='utf-8') as tmp:
    tmp.write('local titles = {\n')
    # last comic at the top to make manual editing easier
    tmp.write('\n'.join(map(lua_item, reversed(sorted(m.items())))))
    tmp.write(dedent("""
    }
    return titles
    -- [[Category:Lua Modules]]
    """))

print("Lua module is ready in file '{}'.".format(output))
