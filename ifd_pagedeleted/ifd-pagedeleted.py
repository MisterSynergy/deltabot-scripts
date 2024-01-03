#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
import re
import sys
from typing import Any

import pywikibot
from pywikibot.data import api

sys.tracebacklimit = 0

SITE = pywikibot.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

TIMESTAMP_FILENAME = f'{expanduser("~")}/jobs/ifd_pagedeleted/ifd-pagedeleted_time.dat'
PREFIX_DICT = {
    'quote' : 'q',
    'news' : 'n',
    'voyage' : 'voy',
    'books' : 'b',
    'source' : 's',
    'species' : 'species',
    'versity' : 'v',
    'media' : 'wmf',
    'data': 'd',
}
CNT_ADDED_LIMIT = 2000  # roughly the limit of cases to add per run


def count_external_id(cc:dict[str, list]) -> int:
    cnt = 0

    for key in cc:
        if cc[key][0].type == 'external-id':
           cnt += 1

    return cnt


def old_edits(old_page_content:str) -> str:
    text = ''

    for line in old_page_content.split('\n'):
        if '|}' in line:
            continue
        text += f'{line}\n'
    
    return text


def new_edits(text) -> tuple[str, str]:
    with open(TIMESTAMP_FILENAME, mode='r', encoding='utf8') as file_handle:
        old_time = file_handle.read().strip()

    rccontinue = f'{old_time}|0'
    cnt_added = 0
    while True:
        params = {
            'action' : 'query',
            'list' : 'recentchanges',
            'rcprop' : 'title|comment|timestamp',
            'rcstart' : old_time,
            'rcdir' : 'newer',
            'rctype' : 'edit',
            'rcnamespace' : '0',
            'rccontinue' : rccontinue,
            'rclimit' : '500',
            'format' : 'json',
        }
        req = api.Request(site=SITE, parameters=params)
        data = req.submit()
        for revision in data.get('query', {}).get('recentchanges', []):
            timestamp = revision.get('timestamp')
            if timestamp is None:
                continue

            comment = revision.get('comment')
            if comment is None:
                continue

            res = re.search('clientsitelink-remove\:1\|\|(.*)wiki(.*) \*\/ (.*)', comment)

            if not res:
                continue

            item = pywikibot.ItemPage(REPO, revision['title'])
            if item.isRedirectPage():
                continue
            if not item.exists():
                continue

            dct = item.get()
            if 'sitelinks' in dct and len(dct['sitelinks']) != 0:
                continue

            nstat = len(dct['claims'])
            nsources = 0

            for p in dct['claims']:
                for c in dct['claims'][p]:
                    for s in c.getSources():
                        keys = list(s.keys())
                        nsources += len(keys) - keys.count('P143')

            source = '' if nsources == 0 else f'<small>({nsources})</small>'
            backlinks = sum(1 for _ in item.backlinks(namespaces=0))
            externalids = count_external_id(dct['claims'])

            if res.group(2) is not None and res.group(2)!='':
                prefix = 'w'
            else:
                prefix = PREFIX_DICT.get(res.group(2), 'w')

            text += f'|-\n| {{{{Q|{revision["title"]}}}}} ([//www.wikidata.org/w/index.php?title={revision["title"]}&action=history hist]) || {nstat} {source} || {backlinks} || {externalids} || [[:{prefix}:{res.group(1).replace("_","-")}:{res.group(3)}]] || {revision["timestamp"]}\n'
            cnt_added += 1

        if 'query-continue' not in data:
             break

        if cnt_added >= CNT_ADDED_LIMIT:
            break

        rccontinue = data.get('query-continue', {}).get('recentchanges', {}).get('rccontinue', 0)

    text += '|}'

    return text, timestamp


def save_to_wiki(page:pywikibot.Page, wikitext:str) -> None:
    page.text = wikitext
    page.save(summary='upd', minor=False)


def main() -> None:
    page = pywikibot.Page(SITE, 'User:Pasleim/Items for deletion/Page deleted')
    wikitext, timestamp = new_edits(old_edits(page.get()))

    save_to_wiki(page, wikitext)
    with open(TIMESTAMP_FILENAME, mode='w', encoding='utf8') as file_handle:
        file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))


if __name__ == '__main__':
    main()
