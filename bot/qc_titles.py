#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot downloads archive.php and updates Lua table on page
'Module:QC/titles'.

Parameters:

-nodownload     If used, do not download fresh archive.php.

-page           Title of the page which should be updated.

-file           File to read new Lua code from.
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
#     3. Generate family file, put it into directory 'pywikibot/families/'.
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

import pywikibot
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.tools.formatter import color_format


DEFAULT_PAGE_TITLE = 'Module:QC/titles'
SOURCE_PAGE = 'archive.php'
SOURCE_URL = 'https://questionablecontent.net/' + SOURCE_PAGE


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

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-file':
            new_data_file = value
        elif option == '-nodownload':
            want_download = False
        elif option == '-page':
            page_title = value
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
            print(lines[140:150])
            # TODO 2. parse using original script qc_titles.py
            pass

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
        new_text = '-- Updated by {}\n'.format(username) + new_text
        summary = 'add comic titles from {} to {}'.format(
                old_last + 1, new_last)
        pywikibot.output(color_format("Summary will be" +
            "\n\t{lightblue}{0}{default}", summary))
        pywikibot.showDiff(old_text, new_text, context=3)

        # check if the edit is sensible
        if old_last > new_last:
            pywikibot.error("Old version is fresher than New version.")
            return False

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
            pywikibot.output("Summary of edit: '{}'".format(summary))
            pywikibot.output("Doing nothing for now... Development still ongoing")
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
