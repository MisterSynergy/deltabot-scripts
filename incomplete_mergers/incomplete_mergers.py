#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any

import pywikibot as pwb
from pywikibot.data import api


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

TIME_FILE = Path.home() / 'jobs/incomplete_mergers/incomplete_mergers_time.dat'


def get_start_time() -> str:
    with open(TIME_FILE, mode='r', encoding='utf8') as file_handle:
        start_time = str(int(file_handle.read())+1)

    return start_time


def get_end_time() -> str:
    end_time = (datetime.now() - timedelta(minutes=10)).strftime('%Y%m%d%H%M%S')

    return end_time


def set_next_start_time(timestamp:str) -> None:
    with open(TIME_FILE, mode='w', encoding='utf8') as file_handle:
        file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))


def get_qids_of_removed_sitelinks(qid:str) -> set[str]:
    params = {
        'action': 'query',
        'prop': 'revisions',
        'titles': qid,
        'rvlimit': 200
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    new_item_qids = []

    for page_id in data.get('query', {}).get('pages', []):
        for revision in data.get('query', {}).get('pages', {}).get(page_id, {}).get('revisions', []):
            matches = re.search(r'wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', revision.get('comment', ''))
            if not matches:
                continue

            try:
                site_wikipedia = pwb.Site(matches.group(1).replace('_', '-'), 'wikipedia')
                page = pwb.Page(site_wikipedia, matches.group(2))
                item_other = pwb.ItemPage.fromPage(page)
            except Exception as exception:  # TODO
                #print(f'Error during finding new hosting item: {exception}')
                continue

            if not item_other.exists():  # TODO: how can this happen?
                continue

            new_item_qids.append(item_other.getID())

    return set(new_item_qids)


def check_item_existence(item:pwb.ItemPage) -> bool:
    return item.exists()


def check_item_not_redirect(item:pwb.ItemPage) -> bool:
    return not item.isRedirectPage()


def check_item_has_n_or_fewer_sitelinks(item:pwb.ItemPage, sitelink_count:int=0) -> bool:
    try:
        item_json = item.get()
    except (pwb.exceptions.IsRedirectPageError, pwb.exceptions.NoPageError):
        return False

    sitelinks = item_json.get('sitelinks', [])
    return (len(sitelinks) <= sitelink_count)


def check_item_has_n_or_fewer_claims(item:pwb.ItemPage, claim_count:int=3) -> bool:
    try:
        item_json = item.get()
    except (pwb.exceptions.IsRedirectPageError, pwb.exceptions.NoPageError):
        return False

    claims = item_json.get('claims', [])
    return (len(claims) <= claim_count)


def check_item_has_n_or_fewer_backlinks(qid:str, backlink_count:int=10) -> bool:
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': qid,
        'blnamespace': 0,
        'bllimit': 11
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    return (len(data.get('query', {}).get('backlinks', [])) <= backlink_count)


def check_item_has_no_backlink_from_wikidata_namespace(qid:str) -> bool:
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': qid,
        'blnamespace': 4,
        'bllimit': 1
    }
    api_request = api.Request(site=SITE, parameters=params)
    data = api_request.submit()
    return (len(data.get('query', {}).get('backlinks', [])) == 0)


def check_item_is_not_in_notability_exemption_category(qid:str) -> bool:
    cat = pwb.Category(SITE, 'Category:Notability policy exemptions')
    category_members = list(cat.articles(recurse=5))
    for page in category_members:
        if qid==page.title()[5:]:  # [5:] because item talk pages are in this categoy, i.e. "Talk:" needs to be ignored
            return False

    return True


def check_all_sitelinks_moved_to_same_target(new_item_qids:set[str]) -> bool:
    return (len(new_item_qids) <= 1)


def check_items_not_linked_to_each_other(qid_1:str, qid_2:str) -> bool:
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

    return True


def check_term_not_in_description(qid_1:str, qid_2:str, *, lang:str='en', search_needle:str='ikimedia') -> bool:
    # check if q1 has "search_needle" in its description but not q2
    item_1 = pwb.ItemPage(REPO, qid_1)
    item_2 = pwb.ItemPage(REPO, qid_2)

    try:
        item_1.get()
        item_2.get()
    except (pwb.exceptions.IsRedirectPageError, pwb.exceptions.NoPageError):
        return False

    if lang not in item_1.descriptions or lang not in item_2.descriptions:
        return False  # void of an description in the chosen language, assume this check hits

    if search_needle in item_1.descriptions.get(lang, '') and search_needle not in item_2.descriptions.get(lang, ''):
        return False

    return True


def merge_items(from_qid:str, to_qid:str) -> None:
    from_item = pwb.ItemPage(REPO, from_qid)
    to_item = pwb.ItemPage(REPO, to_qid)

    try:
        from_item.mergeInto(to_item, ignore_conflicts='description')
    except:  # TODO: handle exceptions properly
        pass

    if not from_item.isRedirectPage():
        clear_item(from_qid)
        from_item.set_redirect_target(to_item, force=True, save=True)


def clear_item(from_qid:str) -> None:
    # get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=SITE, parameters=params)
    data = req.submit()

    # clear item
    params2 = {
        'action': 'wbeditentity',
        'id': from_qid,
        'clear': 1,
        'data': '{}',
        'bot': 1,
        'summary': 'clearing item to prepare for redirect',
        'token': data.get('query', {}).get('tokens', {}).get('csrftoken', '')
    }
    req2 = api.Request(site=SITE, parameters=params2)
    _ = req2.submit()


def process_item(qid:str) -> None:
    #print(f'\n== Processing {qid} ==')
    item = pwb.ItemPage(REPO, qid)

    new_item_qids = get_qids_of_removed_sitelinks(qid)
    if len(new_item_qids) != 1:
        #print(f'Fine because sitelinks are distributed to items "{", ".join([ str(qid) for qid in new_item_qids ])}"')
        return
    target_qid = list(new_item_qids)[0]

    checks = [
        check_item_existence(item),
        check_item_not_redirect(item),
        check_item_has_n_or_fewer_sitelinks(item, 0),
        check_item_has_n_or_fewer_claims(item, 3),
        check_item_has_n_or_fewer_backlinks(qid, 10),
        check_item_has_no_backlink_from_wikidata_namespace(qid),
        check_item_is_not_in_notability_exemption_category(qid),
        check_all_sitelinks_moved_to_same_target(new_item_qids),
        check_items_not_linked_to_each_other(qid, target_qid),
        check_items_not_linked_to_each_other(target_qid, qid),
        check_term_not_in_description(qid, target_qid, lang='en', search_needle='ikimedia'),
        check_term_not_in_description(target_qid, qid, lang='en', search_needle='ikimedia'),
    ]

    if not all(checks):
        #print(f'Do not merge {qid} into {target_qid}')
        return

    #print(f'Merge {qid} into {target_qid}')
    merge_items(qid, target_qid)


def get_revisions(start_time:str, end_time:str) -> Generator[dict[str, Any], None, None]:
    rccontinue = None
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': start_time,
            'rcend': end_time,
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
            if 'comment' not in revision:
                continue
            matches = re.search(r'wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', revision.get('comment', ''))
            if not matches:
                continue

            yield revision

        rccontinue = data.get('continue', {}).get('rccontinue')
        if rccontinue is None:
            break


def main():
    start_time = get_start_time()
    end_time = get_end_time()

    for revision in get_revisions(start_time, end_time):
        timestamp = revision.get('timestamp', '')
        process_item(revision.get('title'))

    set_next_start_time(timestamp)


if __name__=='__main__':
    main()
