#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from pathlib import Path
import re
from typing import Any

import pywikibot
from pywikibot.data import api


SITE = pywikibot.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

CNT_ADDED_LIMIT = 2000  # roughly the limit of cases to add per run

TIMESTAMP_FILENAME = Path.home() / 'jobs/ifd_pagedeleted/ifd-pagedeleted_time.dat'
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


def load_timestamp_from_logfile() -> str:
    with open(TIMESTAMP_FILENAME, mode='r', encoding='utf8') as file_handle:
        old_time = file_handle.read().strip()

    return old_time


def save_timestamp_to_logfile(timestamp:str) -> None:
    with open(TIMESTAMP_FILENAME, mode='w', encoding='utf8') as file_handle:
        file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))


def save_to_wiki(page:pywikibot.Page, wikitext:str) -> None:
    page.text = wikitext
    page.save(summary='upd', minor=False)


def count_external_id_claims(claims:dict[str, list]) -> int:
    cnt = sum([ 1 for pid in claims if claims[pid][0].type=='external-id'])
    return cnt


def parse_revision(revision:dict[str, Any]) -> tuple[dict[str, Any], str]:
    timestamp = revision.get('timestamp')
    if timestamp is None:
        raise ValueError('"timestamp" attribute is missing from revision')

    comment = revision.get('comment')
    if comment is None:
        raise ValueError('"comment" attribute is missing from revision')

    res = re.search(r'clientsitelink-remove\:1\|\|(.*)wiki(.*) \*\/ (.*)', comment)
    if not res:
        return {}, timestamp  # revision to be ignored

    item = pywikibot.ItemPage(REPO, revision.get('title'))

    if not item.exists():
        raise ValueError(f'item "{revision.get("title")}" does not exist')

    if item.isRedirectPage():
        raise ValueError(f'item "{revision.get("title")}" is a redirect page')

    dct = item.get()

    if 'sitelinks' not in dct:
        raise ValueError(f'item "{revision.get("title")}" is missing sitelink information')
    if len(dct['sitelinks']) > 0:
        return {}, timestamp  # item still has sitelinks, do not add to report

    if 'claims' not in dct:
        raise ValueError(f'item "{revision.get("title")}" is missing claim information')

    cnt_statements = len(dct['claims'])
    cnt_sources = 0

    for pid in dct.get('claims', {}):
        for claim in dct.get('claims', {}).get(pid, []):
            for source in claim.getSources():
                keys = list(source.keys())
                cnt_sources += len(keys) - keys.count('P143')

    source = '' if cnt_sources == 0 else f'<small>({cnt_sources})</small>'
    cnt_backlinks = sum(1 for _ in item.backlinks(namespaces=0))
    cnt_externalids = count_external_id_claims(dct['claims'])

    if res.group(2) is not None and res.group(2)!='':
        prefix = 'w'
    else:
        prefix = PREFIX_DICT.get(res.group(2), 'w')

    payload = {
        'title' : revision['title'],
        'cnt_statements' : cnt_statements,
        'source' : source,
        'cnt_backlinks' : cnt_backlinks,
        'cnt_externalids' : cnt_externalids,
        'prefix' : prefix,
        'wiki' : res.group(1).replace("_","-"),
        'sitelink' : res.group(3),
        'timestamp' : revision["timestamp"],
    }

    return payload, timestamp


def query_new_revisions_from_api(old_time:str, rccontinue:str) -> tuple[list[dict[str, Any]], str, str]:
    timestamp = old_time
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

    revisions_to_add:list[dict[str, Any]] = []
    for revision in data.get('query', {}).get('recentchanges', []):
        try:
            revision_to_add, timestamp = parse_revision(revision)
        except ValueError:
            continue

        if len(revision_to_add) > 0:
            revisions_to_add.append(revision_to_add)

    rccontinue = data.get('continue', {}).get('rccontinue', '')

    return revisions_to_add, timestamp, rccontinue


def add_new_edits_to_report(wikitext:str, old_time:str) -> tuple[str, str]:
    rccontinue = f'{old_time}|0'
    all_revisions_to_add:list[dict[str, Any]] = []

    while True:
        revisions_to_add, timestamp, rccontinue = query_new_revisions_from_api(old_time, rccontinue)
        all_revisions_to_add += revisions_to_add  # concat lists

        if rccontinue=='':
            break

        if len(all_revisions_to_add) >= CNT_ADDED_LIMIT:
            break   

    for payload in all_revisions_to_add:
        wikitext += f'\n|-\n| {{{{Q|{payload["title"]}}}}} ([//www.wikidata.org/w/index.php?title={payload["title"]}&action=history hist]) || {payload["cnt_statements"]} {payload["source"]} || {payload["cnt_backlinks"]} || {payload["cnt_externalids"]} || [[:{payload["prefix"]}:{payload["wiki"]}:{payload["sitelink"]}]] || {payload["timestamp"]}'

    wikitext += '\n|}'

    return wikitext, timestamp


def main() -> None:
    page = pywikibot.Page(SITE, 'User:Pasleim/Items for deletion/Page deleted')
    page_wikitext = page.get()
    page_wikitext = page_wikitext.replace('\n|}', '')  # remove end of table syntax

    old_time = load_timestamp_from_logfile()
    wikitext, timestamp = add_new_edits_to_report(page_wikitext, old_time)

    save_to_wiki(page, wikitext)
    save_timestamp_to_logfile(timestamp)


if __name__ == '__main__':
    try:
        main()
    except KeyError as exception:
        print(exception)
