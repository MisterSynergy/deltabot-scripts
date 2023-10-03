#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime, timedelta
from os.path import expanduser
import re

import pywikibot as pwb
from pywikibot.data import api


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

TIME_FILE = f'{expanduser("~")}/jobs/incomplete_mergers/incomplete_mergers_time.dat'


def addition_check(qid_1:str, qid_2:str) -> bool:
    # only pass if not linked together
    params = {
        'action': 'query',
        'titles': qid_1,
        'prop': 'links',
        'pllimit': 500
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    for page_id in data.get('query', {}).get('pages', []):
        for page in data.get('query', {}).get('pages', {}).get(page_id, {}).get('links', []):
            if qid_2 == page.get('title', ''):
                return False

    # check if q1 has wikimedia in its description but not q2
    item_1 = pwb.ItemPage(REPO, qid_1)
    item_1.get()

    item_2 = pwb.ItemPage(REPO, qid_2)
    item_2.get()

    if 'en' in item_1.descriptions and 'en' in item_2.descriptions:
        if 'ikimedia' in item_1.descriptions.get('en', '') and 'ikimedia' not in item_2.descriptions.get('en', ''):
            return False

    return True


def merge(from_qid:str, to_qid:str) -> None:
    if addition_check(from_qid, to_qid) is False:
        return

    from_item = pwb.ItemPage(REPO, from_qid)
    to_item = pwb.ItemPage(REPO, to_qid)

    try:
        from_item.mergeInto(to_item, ignore_conflicts='description')
    except:
        pass

    if not from_item.isRedirectPage():
        clear_item(from_qid)
        from_item.set_redirect_target(to_item, force=True, save=True)


def clear_item(fromId):
    # get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=SITE, parameters=params)  # upd 2022-12-05 by User:MisterSynergy from **params to parameters=params
    data = req.submit()
    # clear item
    params2 = {
        'action': 'wbeditentity',
        'id': fromId,
        'clear': 1,
        'data': '{}',
        'bot': 1,
        'summary': 'clearing item to prepare for redirect',
        'token': data['query']['tokens']['csrftoken']
    }
    req2 = api.Request(site=SITE, parameters=params2)
    data2 = req2.submit()


def check(qid:str) -> None:
    item = pwb.ItemPage(REPO, qid)

    if not item.exists():
        return
    if item.isRedirectPage():
        return

    # ignore items with sitelinks and more than 3 claims
    item_json = item.get()
    if len(item_json.get('sitelinks', [])) > 0:
        return
    if len(item_json.get('claims', [])) > 3:
        return

    # ignore items with more than 10 backlinks
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': qid,
        'blnamespace': 0,
        'bllimit': 11
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    if len(data.get('query', {}).get('backlinks', [])) > 10:
        return

    # ignore items with link to WD namespace
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': qid,
        'blnamespace': 4,
        'bllimit': 1
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    if len(data.get('query', {}).get('backlinks', [])) > 0:
        return

    # ignore items in Category:Notability policy exemptions
    cat = pwb.Category(SITE, 'Category:Notability policy exemptions')
    category_members = list(cat.articles(recurse=5))
    for page in category_members:
        if qid==page.title()[5:]:  # TODO: why [5:]?
            return

    # ignore items where all removed sitelinks are not added to the same new item
    params = {
        'action': 'query',
        'prop': 'revisions',
        'titles': qid,
        'rvlimit': 200
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    qid_other = None

    for page_id in data.get('query', {}).get('pages', []):
        for revision in data.get('query', {}).get('pages', {}).get(page_id, {}).get('revisions', []):
            matches = re.search('wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', revision.get('comment', ''))
            if not matches:
                continue

            try:
                site_wikipedia = pwb.Site(matches.group(1).replace('_', '-'), 'wikipedia')
                page = pwb.Page(site_wikipedia, matches.group(2))
                item_other = pwb.ItemPage.fromPage(page)
            except:
                continue

            if not item_other.exists():
                continue

            qid_candidate = item_other.getID()
            if not qid_other or qid_other == qid_candidate:
                qid_other = qid_candidate
            else:
                continue

    if qid_other is None:
        return

    merge(qid, qid_other)


def main():
    with open(TIME_FILE, mode='r', encoding='utf8') as file_handle:
        old_time_str = str(int(file_handle.read())+1)

    new_time = datetime.now() - timedelta(minutes=10)
    new_time_str = new_time.strftime('%Y%m%d%H%M%S')

    rccontinue = None
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': old_time_str,
            'rcend': new_time_str,
            'rcdir': 'newer',
            'rctype': 'edit',
            'rcnamespace': 0,
            'rcshow': '!bot',
            'rclimit': 500,
            'rccontinue': rccontinue
        }
        if rccontinue is None:  # remove parameter for first request
            params.pop('rccontinue')

        api_request = api.Request(site=SITE, parameters=params)
        data = api_request.submit()
        for revision in data.get('query', {}).get('recentchanges', {}):
            timestamp = revision.get('timestamp', '')
            if 'comment' not in revision:
                continue

            matches = re.search('wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', revision.get('comment', ''))
            if not matches:
                continue

            check(revision.get('title'))

        if 'query-continue' not in data:
            break

        rccontinue = data.get('query-continue', {}).get('recentchanges', {}).get('rccontinue', '')

    with open(TIME_FILE, mode='w', encoding='utf8') as file_handle:
        file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))


if __name__=='__main__':
    main()
