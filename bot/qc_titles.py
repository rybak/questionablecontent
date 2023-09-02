#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot parses HTML of https://questionablecontent.net/archive.php
and updates Lua table on the page 'Module:QC/titles'.

Parameters:

-summary        Extra message to add to the edit summary.

-auto           Run bot automatically, without asking for confirmation of edits. This is useful for running the bot
                using some kind of scheduler, like crontab.

-nodownload     If used, do not download fresh archive.php.

-page           Title of the page which should be updated.

-file           File to read new Lua code from.

Example:

    python3 pwb.py qc_titles '-summary:extra message'
"""

#
# © Andrei Rybak, 2019-2023
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
from socket import timeout
import os.path
from datetime import datetime
from textwrap import dedent
import time
import subprocess

import pywikibot
from pywikibot.bot_choice import QuitKeyboardInterrupt


DEFAULT_PAGE_TITLE = 'Module:QC/titles'
SOURCE_PAGE = 'archive.php'
SOURCE_URL = 'https://questionablecontent.net/' + SOURCE_PAGE
MIN_AUTO_SECONDS = 60 * 10
MAX_AUTO_SECONDS = 60 * 60 * 6
DEBUG = False
if DEBUG:
    MIN_AUTO_SECONDS = 10
    MAX_AUTO_SECONDS = 30


def grep_lua_last_comic(text):
    last_comic_m = re.search('\[([0-9]{4,6})\]', text)
    last_comic = last_comic_m.group(1)
    return int(last_comic)


def is_fresh(filename):
    try:
        mt = os.path.getmtime(filename)
        last_modified = datetime.fromtimestamp(mt)
        delta = datetime.now() - last_modified
        return delta.total_seconds() < MIN_AUTO_SECONDS
    except OSError:
        return False


def download(url: str, filename: str) -> str:
    pywikibot.output("Downloading {}...".format(filename))
    try:
        req = urllib.request.Request(url, headers={'User-Agent' : "Magic"})
        response = urllib.request.urlopen(req, timeout=10)
        data = response.read().decode('utf-8', errors='ignore')
    except urllib.error.URLError as e:
        pywikibot.error(str(e))
        return None
    except urllib.error.HTTPError as e:
        pywikibot.error(str(e))
        return None
    except timeout as e:
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
            pywikibot.output("Missing comic <<red>>#{}<<default>>.".format(n))

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
    # has two titles in archive
    m[1496] = "Tetsuoooooo! Kanedaaaaaaaaa!"
    # have incorrect title in archive
    m[1464] = "Cheers"
    m[1499] = "One Year Anniversary Special"
    m[1601] = m[3]
    m[1645] = "Unexpected Windfall"
    m[1758] = "Oh Shit"
    m[2255] = "Butts Disease"

    # HTML encode these two just in case
    m[2680] = "&gt;:|"  # angry emoticon ">:|"
    m[3911] = "&lt; body &gt;"  # body tag "< body >"

    # missing diacritic in the archive
    m[3219] = 'Sláinte'
    # typo in the archive
    m[4032] = 'Friend To The Lowly'
    # extra comic number in the archive
    m[4087] = 'With Utmost Precision'
    # typo in the archive
    m[4230] = 'To Be Truthful'

    # corrupted titles
    m[2409] = 'Chaîne Des Puys'
    m[2412] = 'Tschüss'
    m[4029] = 'A New, Friendly You™'

    pywikibot.output("Got <<aqua>>{}<<default>> comic titles after cleanup.".format(len(m)))


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
        -- [[Category:Lua modules]]"""))

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
            time.sleep(config.retry_wait)
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


def update_titles(new_data_file: str, want_download: bool, page_title: str, extra_summary: str,
        automatic: bool) -> bool:
    """
    Perform a single update of page 'page_title' using 'archive.php' of QC website.
    """
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
        if DEBUG:
            lines = data.splitlines()
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
    pywikibot.output("Old version goes till <<lightred>>{}<<default>>.".format(old_last))
    pywikibot.output("New version goes till <<lightgreen>>{}<<default>>.".format(new_last))
    username = site.username()
    new_text = '-- Updated by {}\n'.format(username) + new_text.rstrip()

    # check if the edit is sensible
    if old_text == new_text:
        pywikibot.output("No changes. Nothing to do.")
        return True
    if old_last >= new_last and old_text == new_text:
        pywikibot.output("Current version already has {0}." \
                .format(new_last) + " Nothing to do.")
        return True

    pywikibot.showDiff(old_text, new_text)

    summary = None
    if old_last + 1 == new_last:
        summary = 'add comic title for {}'.format(new_last)
    elif new_last > old_last:
        summary = 'add comic titles from {} to {}'.format(
                old_last + 1, new_last)
    else:
        summary = 'correcting older comic titles'
        while not extra_summary:
            extra_summary = pywikibot.input("Please add extra summary message:")
    if extra_summary:
        summary = summary + " ({})".format(extra_summary)
    pywikibot.output("Summary will be" +
        "\n\t<<lightblue>>{}<<default>>".format(summary))

    try:
        if automatic:
            choice = 'y'
        else:
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


def notify_user():
    try:
        app_name = os.path.basename(__file__)
    except:
        app_name = 'QC Wiki bot'
    error_title = 'Warning'
    error_message = 'Error in Questionable Content Wiki bot.'
    full_message = error_title + '. ' + error_message

    print('\a')  # ASCII bell
    try:
        # On Linuxes---using binary notify-send
        # https://stackoverflow.com/a/44027111/1083697
        subprocess.call(['notify-send', app_name, full_message, '--icon=dialog-error'])
    except:
        pass
    try:
        # On Ubuntu---using speech-to-text generator
        # https://stackoverflow.com/a/29590673/1083697
        # start speech dispatcher
        subprocess.call(['speech-dispatcher'])
        # option -r -50 slows down speech a bit.
        subprocess.call(['spd-say', '-r', '-50', full_message])
    except:
        pass
    try:
        # pip3 install plyer
        # Cross-platform python library
        # https://stackoverflow.com/a/42085439/1083697
        from plyer import notification
        notification.notify(
            title=error_title,
            message=error_message,
            app_name=app_name
        )
    except ImportError:
        pass
    try:
        # pip3 install win10toast
        # https://stackoverflow.com/a/49892758/1083697
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(app_name, full_message, duration=10)
    except ImportError:
        pass


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """

    pywikibot.output("Start: <<white>>{}<<default>>".format(datetime.now()))

    local_args = pywikibot.handle_args(args)

    # default values for options
    new_data_file = 'data.lua'
    want_download = True
    page_title = DEFAULT_PAGE_TITLE
    extra_summary = None
    automatic = False

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
        elif option == '-auto':
            automatic = True
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
    if automatic and not want_download:
        pywikibot.error("Flags -auto and -nodownload are not compatible.")
        return False
    if want_download:
        pywikibot.output("Will download '{}'.".format(SOURCE_PAGE))
    pywikibot.output("Will edit page '{}'.".format(page_title))

    try:
        sleep_on_error_seconds = MIN_AUTO_SECONDS
        while True:
            updated = update_titles(new_data_file, want_download, page_title, extra_summary, automatic)
            if updated:
                pywikibot.output("Update successful.")
                with open('qc_titles_success.tmp', 'w') as f:
                    f.write(str(datetime.now()))
                break
            pywikibot.error("Could not update.")
            with open('qc_titles_failure.tmp', 'w') as f:
                f.write(str(datetime.now()))
            notify_user()
            pywikibot.output("Sleeping for {} seconds.".format(sleep_on_error_seconds))
            try:
                time.sleep(sleep_on_error_seconds)
                # after using current value of sleep_on_error_seconds, increase it until max
                sleep_on_error_seconds *= 2
                if sleep_on_error_seconds > MAX_AUTO_SECONDS:
                    sleep_on_error_seconds = MAX_AUTO_SECONDS
            except KeyboardInterrupt:
                pywikibot.output("Sleep interrupted by user. Proceeding to next update.")
    except KeyboardInterrupt:
        pywikibot.output("Interrupted by user. Aborting.")
        return False
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
    finally:
        pywikibot.output("Finish: <<white>>{}<<default>>".format(datetime.now()))


if __name__ == '__main__':
    main()
