#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot parses HTML of https://questionablecontent.net/archive.php
and updates Lua table on the page 'Module:QC/titles'.

Parameters:

-nodownload     If used, do not download fresh archive.php.

-page           Title of the page which should be updated.

-file           File to read new Lua code from.

-summary        Extra message to add to the edit summary.
"""

#
# © Andrei Rybak, 2019
# Written for Questionable Content Wiki
#
# Distributed under the terms of the MIT license.
#
# Usage:
#     1. Install pywikibot (see URL below).
#     2. Generate user-config.py for your account.
#     3. Put qcwiki_family.py into directory 'pywikibot/families/'.
#        You can also generate family file yourself using script
#        'generate_family_file.py' provided in Pywikibot installation.
#     4. Put this script into 'scripts/userscripts/' directory.
#     5. Run bot with command:
#
#          python pwb.py qc_titles
#
# https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
# For more info about Pywikibot usage see
# https://www.mediawiki.org/wiki/Manual:Pywikibot/Use_on_third-party_wikis
#

from __future__ import absolute_import, division, unicode_literals

import sys
import re
import urllib.request
import os.path
import datetime
from textwrap import dedent

import pywikibot
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.tools.formatter import color_format


DEFAULT_PAGE_TITLE = 'Module:QC/titles'
SOURCE_PAGE = 'archive.php'
SOURCE_URL = 'https://questionablecontent.net/' + SOURCE_PAGE
DEBUG = False


def grep_lua_last_comic(text):
    last_comic_m = re.search('\[([0-9]{4,6})\]', text)
    last_comic = last_comic_m.group(1)
    return int(last_comic)


def is_fresh(filename):
    try:
        mt = os.path.getmtime(filename)
        last_modified = datetime.datetime.fromtimestamp(mt)
        delta = datetime.datetime.now() - last_modified
        return delta.total_seconds() < 3600
    except OSError:
        return False


def download(url: str, filename: str) -> str:
    pywikibot.output("Downloading {}...".format(filename))
    try:
        req = urllib.request.Request(url, headers={'User-Agent' : "Magic"})
        response = urllib.request.urlopen(req)
        data = response.read().decode('utf-8', errors='ignore')
    except urllib.error.URLError as e:
        pywikibot.error(str(e))
        return None
    # Write data to file
    with open(filename, 'w') as f:
        f.write(data)
        f.close()
        pywikibot.output("Updated local copy of '{}'.".format(filename))
    return data


def url(n):
    return 'https://www.questionablecontent.net/view.php?comic=' + str(n)


def parse_archive(f: str, output: str = "data.lua"):
    ls = []
    with open(f, encoding='utf-8', errors='ignore') as tmp:
        ls = tmp.readlines()

    pywikibot.output("Parsing '{}'...".format(f))
    pywikibot.output("Number of lines: {}.".format(len(ls)))
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
    pywikibot.output("Got {} raw results.".format(len(res)))

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
            pywikibot.output(color_format("Missing comic {red}#{0}{default}.", n))

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

    pywikibot.output(color_format("Got {aqua}{0}{default} comic titles after cleanup.", len(m)))


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
        -- [[Category:Lua Modules]]"""))

    pywikibot.output("Lua module is ready in file '{}'.".format(output))


def put_text(page, new, summary, count, asynchronous=False):
    """
    Save the new text. Boilerplate copied from scripts/add_text.py.

    © Pywikibot team, 2013-2019
    """
    page.text = new
    try:
        page.save(summary=summary, asynchronous=asynchronous,
                  minor=page.namespace() != 3)
    except pywikibot.EditConflict:
        pywikibot.output('Edit conflict! skip!')
    except pywikibot.ServerError:
        if count <= config.max_retries:
            pywikibot.output('Server Error! Wait..')
            pywikibot.sleep(config.retry_wait)
            return None
        else:
            raise pywikibot.ServerError(
                'Server Error! Maximum retries exceeded')
    except pywikibot.SpamfilterError as e:
        pywikibot.output(
            'Cannot change {} because of blacklist entry {}'
            .format(page.title(), e.url))
    except pywikibot.LockedPage:
        pywikibot.output('Skipping {} (locked page)'.format(page.title()))
    except pywikibot.PageNotSaved as error:
        pywikibot.output('Error putting page: {}'.format(error.args))
    else:
        return True
    return False


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """

    local_args = pywikibot.handle_args(args)

    # default values for options
    new_data_file = 'data.lua'
    want_download = True
    page_title = DEFAULT_PAGE_TITLE
    extra_summary = None

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-file':
            new_data_file = value
        elif option == '-nodownload':
            want_download = False
        elif option == '-page':
            page_title = value
        elif option == '-summary':
            extra_summary = value
        else:
            pywikibot.warning("Unrecognized option {}".format(option))


    def check_option(option, value):
        if not value:
            pywikibot.error("Missing argument for option '{}'".format(option))
            return False
        return True


    if not check_option('-file', new_data_file) or \
            not check_option('-page', page_title):
        pywikibot.error("Aborting.")
        return False
    if want_download:
        pywikibot.output("Will download '{}'.".format(SOURCE_PAGE))
    pywikibot.output("Will edit page '{}'.".format(page_title))

    try:
        if want_download:
            if is_fresh(SOURCE_PAGE):
                pywikibot.output("Found fresh file '{}'".format(SOURCE_PAGE))
                with open(SOURCE_PAGE, 'r', encoding='utf-8', errors='ignore') as f:
                    data = f.read()
            else:
                data = download(SOURCE_URL, SOURCE_PAGE)
            if data is None:
                pywikibot.error("Could not download '{}'.".format(SOURCE_PAGE))
                return False
            lines = data.splitlines()
            if DEBUG:
                print(lines[140:150])
            parse_archive(SOURCE_PAGE, new_data_file)

        site = pywikibot.Site()
        page = pywikibot.Page(site, page_title)
        old_text = page.get()
        new_text = None
        try:
            with open(new_data_file, 'r', encoding='utf-8') as f:
                new_text = f.read()
        except:
            pass
        if new_text is None:
            pywikibot.error("Could not read new text to upload. Aborting.")
            return False

        old_last = grep_lua_last_comic(old_text)
        new_last = grep_lua_last_comic(new_text)

        # report what will happen
        pywikibot.output(color_format(
            "Old version goes till {lightred}{0}{default}.", old_last))
        pywikibot.output(color_format(
            "New version goes till {lightgreen}{0}{default}.", new_last))
        username = site.username()
        new_text = '-- Updated by {}\n'.format(username) + new_text.rstrip()
        summary = None
        if old_last + 1 == new_last:
            summary = 'add comic title for {}'.format(new_last)
        else:
            summary = 'add comic titles from {} to {}'.format(
                    old_last + 1, new_last)
        if extra_summary:
            summary = summary + " ({})".format(extra_summary)
        pywikibot.showDiff(old_text, new_text)
        pywikibot.output(color_format("Summary will be" +
            "\n\t{lightblue}{0}{default}", summary))

        # check if the edit is sensible
        if old_text == new_text:
            pywikibot.output("No changes. Nothing to do.")
            return True
        if old_last >= new_last:
            pywikibot.output("Current version already has {0}." \
                    .format(new_last) + " Nothing to do.")
            return True

        try:
            choice = pywikibot.input_choice(
                "Do you want to accept these changes?",
                [('Yes', 'y'), ('No', 'n'),
                 ('open in Browser', 'b')], 'n')
        except QuitKeyboardInterrupt:
            sys.exit("User quit bot run.")

        if choice == 'n':
            pywikibot.output("Okay, doing nothing.")
            return False
        elif choice == 'b':
            pywikibot.bot.open_webbrowser(page)
        elif choice == 'y':
            error_count = 0
            while True:
                result = put_text(page, new_text, summary, error_count)
                if result is not None:
                    return result
                error_count += 1
            return True

    except pywikibot.NoPage:
        pywikibot.error("{} doesn't exist, abort!".format(page.title()))
        return False
    except pywikibot.IsRedirectPage:
        pywikibot.error("{} is a redirect, abort!".format(page.title()))
        return False
    except pywikibot.Error as e:
        pywikibot.bot.suggest_help(exception=e)
        return False
    else:
        return True


if __name__ == '__main__':
    main()
