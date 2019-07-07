#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot automatically fills in empty image pages.

Parameters:

-summary        Extra message to add to the edit summary.

Example:

    python3 pwb.py qc_titles '-summary:extra message'
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
#          python pwb.py qc_images
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
import requests

import pywikibot
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.tools.formatter import color_format
from pywikibot.textlib import getCategoryLinks
from pywikibot.textlib import extract_sections


DEBUG = False


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


def parse_archive(f: str, output: str = "data.lua"):
    ls = []
    with open(f, encoding='utf-8', errors='ignore') as tmp:
        ls = tmp.readlines()

    pywikibot.output("Parsing '{}'...".format(f))
    pywikibot.output("Number of lines: {}.".format(len(ls)))
    # parse every line to a list of tuples (<number>, <title>)
    res = []
    for line in ls:
        pass
    pywikibot.output("Got {} raw results.".format(len(res)))

    if DEBUG:
        pass

    # pywikibot.output(color_format("Missing comic {red}#{0}{default}.", n))
    m = {}
    pywikibot.output(color_format("Got {aqua}{0}{default} comic titles after cleanup.", len(m)))
    # pywikibot.output("Lua module is ready in file '{}'.".format(output))


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


ROOT_URL = 'https://questionablecontent.fandom.com/'
REST_URL = ROOT_URL + 'api/v1/'
rest_session = requests.Session()


def request_list():
    offset = ''
    url = REST_URL + 'Articles/List'
    first = True
    result = {}
    while first or len(result.get('items', [])) > 0:
        first = False
        parameters = {
            'expand': 1,
            'limit': 10,
            # Comma-separated namespace ids, see more: http://community.wikia.com/wiki/Help:Namespaces
            'namespaces': '6',  # File namespace id = 6
            'offset': offset   # Lexicographically minimal article title.
        }
        r = rest_session.get(url, params=parameters)
        result = None
        if r.status_code != 200:
            print(r)
            print("Download failed for {}".format(r.url))
            if r.status_code == 401:
                print("Wrong password")
                # reset_auth()
                # go into while True again, ask for password one more time
                continue
            if r.status_code == 403:
                # reset_auth()
                continue
            if r.status_code == 404:
                print("Not found {}".format(r.url))
        else:
            print("Request successful: " + r.url)
            result = r.json()
        if result is None:
            break
        pywikibot.output("Basepath: {0}".format(result['basepath']))
        for item in result['items']:
            yield item
        offset = result.get('offset', '')


def request_pages():
    for p in request_list():
        snippet = p['abstract']
        if 'QC image' in snippet or 'File information' in snippet:
            continue
        last_rev = p['revision']
        print(last_rev)
        if 'AndrybakBot' == last_rev['user']:
            # skip, if previous edit has probably fixed the page
            continue
        yield p


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """

    local_args = pywikibot.handle_args(args)

    # default values for options
    extra_summary = None

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-summary':
            extra_summary = value
        else:
            pywikibot.warning("Unrecognized option {}".format(option))


    def check_option(option, value):
        if not value:
            pywikibot.error("Missing argument for option '{}'".format(option))
            return False
        return True


    page_number_regex = re.compile('\|([1-9][0-9]*)\}')
    filename_number_regex = re.compile('([1-9][0-9]*)')
    templates_ready = ['QC image', 'File information', 'Self']
    site = pywikibot.Site()
    looked_at = set()
    pages = request_pages()
    for p in pages:
        if p['title'] in looked_at:
            pywikibot.output("Done.")
            break
        else:
            looked_at.add(p['title'])
        try:
            page_title = 'File:' + p['title']
            page = pywikibot.Page(site, page_title)
            click_url = ROOT_URL + 'wiki/' + page.title(underscore=True)
            pywikibot.output("Page '{0}', id={1} | {2}".format(page_title, p['id'], click_url))
            ts = page.templatesWithParams()
            if len(ts) > 0:
                found_ready = False
                for t in ts:
                    for r in templates_ready:
                        if r in t[0].title():
                            pywikibot.output(color_format("Page {lightgreen}{0}{default} has template: {1}",
                                page_title, t[0]))
                            found_ready = True
                            break
                if found_ready:
                    pywikibot.output("\tSkipping.")
                    continue

            old_text = page.get()
            # categories = getCategoryLinks(old_text, site)
            # categories_text = '\n'.join(map(lambda c:c.aslink(), categories))
            (header, body, footer) = extract_sections(old_text, site)
            summary = None
            licensing = None
            description = None
            for section in body:
                if 'ummary' in section[0] or 'escription' in section[0]:
                    summary = section[1]
                if 'icens' in section[0]:
                    licensing = section[1]
            got_summary_from_header = False
            if summary is None:
                got_summary_from_header = True
                summary = header

            new_text = None
            pywikibot.output(color_format("Editing page {lightblue}{0}{default}.", page_title))
            if summary is not None and len(summary.strip()) > 0:
                summary = summary.strip()
                pywikibot.output("Have \"Summary\":\n\t{}".format(summary))
                i = summary.find('{')
                if i > 0:
                    summary = summary[0:i]
                i = summary.find(' in ')
                if i > 0:
                    summary = summary[0:i]
                summary = summary.strip()
                if summary[-1] == '.':
                    summary = summary[0:-1]
                pywikibot.output("Will have \"Summary\":\n\t{}".format(summary))
                choice = pywikibot.input_choice("Is it a good summary?",
                    [('Yes', 'y'), ('No', 'n'), ('open in Browser', 'b')], 'n')
                if choice == 'y':
                    description = summary
                elif choice == 'n':
                    pass
                elif choice == 'b':
                    pywikibot.bot.open_webbrowser(page)
            if description is None:
                pywikibot.output("Type '[s]kip' to skip the image completely.")
                description = pywikibot.input("Please describe the file:")
                if description in ['s', 'skip']:
                    continue
            if licensing is not None:
                pywikibot.output("Have \"Licensing\":\n\t{}".format(licensing.strip()))

            comic_num = None
            m = page_number_regex.search(old_text)
            if m:
                try:
                    comic_num = int(m.group(1))
                except:
                    pass
            if comic_num is None:
                m = filename_number_regex.search(page.title())
                if m:
                    try:
                        comic_num = int(m.group(1))
                    except:
                        pass
            if comic_num is not None:
                pywikibot.output("Have comic #:\n\t{}".format(comic_num))
                choice = pywikibot.input_choice("Is it a good comic number?",
                    [('Yes', 'y'), ('No', 'n'), ('open in Browser', 'b')], 'n')
                if choice == 'y':
                    pass
                else:
                    comic_num = None
                if choice == 'b':
                    pywikibot.bot.open_webbrowser(page)
            while comic_num is None:
                try:
                    pywikibot.output("Need comic number. Type 0 to skip")
                    comic_num = int(pywikibot.input("Comic number: "))
                except ValueError:
                    pass
            if comic_num == 0:
                comic_num = ''

            new_text = dedent("""
                == Summary ==
                {{{{QC image|{0}|{1}}}}}

                == Licensing ==
                {{{{Fairuse}}}}
                """.format(description, comic_num)).strip()
            header = header.strip()
            if not got_summary_from_header and len(header) > 0:
                new_text = header + '\n\n' + new_text
            footer = footer.strip()
            if len(footer) > 0:
                new_text += '\n\n' + footer

            # check if the edit is sensible
            if old_text == new_text:
                pywikibot.output("No changes. Nothing to do.")
                continue
            # report what will happen
            pywikibot.showDiff(old_text, new_text, context=3)

            summary = "add [[Template:QC image]]; mark as fair use " + \
                "([[User:AndrybakBot#Image maintenance|Image maintenance bot task]])"
            if extra_summary:
                summary = summary + " ({})".format(extra_summary)
            pywikibot.output(color_format("Summary will be" +
                "\n\t{lightblue}{0}{default}", summary))
            choice = pywikibot.input_choice(
                "Do you want to accept these changes?",
                [('Yes', 'y'), ('No', 'n'), ('open in Browser', 'b')], 'n')
            # if choice == 'y':
            #     pywikibot.output("Test run, doing nothing.")
            #     continue
            if choice == 'n':
                pywikibot.output("Okay, doing nothing.")
                continue
            elif choice == 'b':
                pywikibot.bot.open_webbrowser(page)
            elif choice == 'y':
                error_count = 0
                while True:
                    result = put_text(page, new_text, summary, error_count)
                    if result is not None:
                        pywikibot.output("Got result of saving: {}".format(result))
                        break
                    error_count += 1
                continue
            elif choice == 'q':
                break

        except pywikibot.NoPage:
            pywikibot.error("{} doesn't exist, skipping.".format(page.title()))
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.error("{} is a redirect, skipping".format(page.title()))
            continue
        except pywikibot.Error as e:
            pywikibot.bot.suggest_help(exception=e)
            continue
        except QuitKeyboardInterrupt:
            sys.exit("User quit bot run.")
        else:
            pass


if __name__ == '__main__':
    main()
