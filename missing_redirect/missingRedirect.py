#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any, Optional

import pywikibot
from pywikibot.data import api


SITE = pywikibot.Site('wikidata', 'wikidata')
SITE.login()
REPO = SITE.data_repository()

EXEMPTION_CATEGORY = pywikibot.Category(SITE, 'Category:Notability policy exemptions')
EXEMPTION_LIST = list(EXEMPTION_CATEGORY.articles(recurse=5))

TIME_FILE = Path.home() / 'jobs/missing_redirect/missingRedirect_time.dat'


def merge(from_id:str, to_id:str) -> None:
    fromItem = pywikibot.ItemPage(REPO, from_id)
    toItem = pywikibot.ItemPage(REPO, to_id)
    fromItem.mergeInto(toItem, ignore_conflicts='description')
    clear_item(from_id)
    fromItem.set_redirect_target(toItem, force=True, save=True)


def clear_item(from_id:str) -> None:
    token_params = {
        'action': 'query',
        'meta': 'tokens'
    }
    token_request = api.Request(site=SITE, parameters=token_params)
    token_data = token_request.submit()

    params = {
        'action' : 'wbeditentity',
        'id' : from_id,
        'clear' : 1,
        'data' : '{}',
        'bot' : 1,
        'summary' : 'clearing item to prepare for redirect',
        'token' : token_data.get('query', {}).get('tokens', {}).get('csrftoken', '')
    }
    request = api.Request(site=SITE, parameters=params)
    request.submit()


def process_revision(revision:dict[str, Any]) -> Optional[str]:
    processed_timestamp = revision.get('timestamp')
    revision_comment = revision.get('comment')
    if revision_comment is None:
        return processed_timestamp

    res = re.search('\/\* wbmergeitems-to:0\|\|(Q[0-9]+) \*\/', revision_comment)
    if not res:
        return processed_timestamp

    #ignore items in Category:Notability policy exemptions
    for list_entry in EXEMPTION_LIST:
        if revision.get('title') == list_entry.title()[5:]:  # Talk: pages are categorized here
            return processed_timestamp

    try:
        merge(revision['title'], res.group(1))
    except Exception as exception:  # TODO
        print(exception)

    return processed_timestamp


def make_api_request(old_time:str, new_time:str, rccontinue:str) -> tuple[Optional[str], Optional[str]]:
    params = {
        'action' : 'query',
        'list' : 'recentchanges',
        'rcprop' : 'title|comment|timestamp',
        'rcstart' : old_time,
        'rcend' : new_time,
        'rcdir' : 'newer',
        'rclimit' : 500,
        'rctype' : 'edit',
        'rcnamespace' : 0,
        'rctoponly' : 1,
        'rccontinue' : rccontinue,
    }
    request = api.Request(site=SITE, parameters=params)
    data = request.submit()

    processed_timestamp = None
    for revision in data.get('query', {}).get('recentchanges', {}):
        processed_timestamp = process_revision(revision)

    rccontinue = data.get('query-continue', {}).get('recentchanges', {}).get('rccontinue')
    return rccontinue, processed_timestamp


def main():
    with open(TIME_FILE, 'r') as file_handle:
        done_until_str = file_handle.read()

    old_time_str = (datetime.strptime(done_until_str, '%Y%m%d%H%M%S') \
        + timedelta(seconds=1)).strftime('%Y%m%d%H%M%S')

    now = datetime.now()
    new_time = now - timedelta(minutes=10)
    new_time_str = new_time.strftime('%Y%m%d%H%M%S')
    rccontinue = old_time_str+'|0'
    while True:
        rccontinue, timestamp = make_api_request(old_time_str, new_time_str, rccontinue)
        if rccontinue is None:
            break

    if timestamp is not None:
        with open(TIME_FILE, 'w') as file_handle:
            file_handle.write(re.sub(r'\:|\-|Z|T', '', timestamp))


if __name__ == '__main__':
    main()
