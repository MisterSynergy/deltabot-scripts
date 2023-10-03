#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime, timedelta
import re
from typing import Optional

import pywikibot as pwb
from pywikibot.data import api


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()


def check_item(qid:str) -> Optional[str]:
    item = pwb.ItemPage(REPO, qid)

    if not item.exists():
        return None

    if item.isRedirectPage():
        return None

    dict = item.get()
    if len(dict['sitelinks']) > 0:  # has sitelinks, is notable
        return None

    if len(dict['claims']) >= 3:  # has 3 or more claims
        return None

    if sum(1 for _ in item.backlinks(namespaces=0)) > 0:  # has backlinks
        return None

    claim_cnt = len(dict['claims'])
    if claim_cnt == 1:
        return f'{{{{Q|{qid}}}}} (1 statement)<br />\n'

    return f'{{{{Q|{qid}}}}} ({claim_cnt} statements)<br />\n'


def purge_report_page(old_text:str) -> str:
    new_text = ''
    date:Optional[str] = None

    for line in old_text.split('\n'):
        if '===' in line:
            date = line
            continue

        if '{{Q|' not in line:
            continue

        matches = re.search(r'\{\{Q\|Q?([0-9]*)\}\}', line)
        if not matches:
            continue

        qid_numerical = matches.group(1)

        item_text = check_item(f'Q{qid_numerical}')
        if item_text is None:
            continue

        if date:
            new_text += f'{date}\n'
            date = None

        new_text += item_text

    return new_text


def check_items_from_yesterday() -> str:
    new_text = ''

    yesterday = datetime.now() - timedelta(days=1)
    date = yesterday.strftime("%Y%m%d")
    date2 = yesterday.strftime("%Y-%m-%d")

    new_date_added = False
    rccontinue = f'{date}000000|0'

    while True:
        params = {
            'action' : 'query',
            'list' : 'recentchanges',
            'rctype' : 'new',
            'rcprop' : 'title',
            'rcstart' : f'{date}000000',
            'rcend' : f'{date}235959',
            'rcdir' : 'newer',
            'rclimit' : '500',
            'rcnamespace' : '0',
            'rcshow' : '!patrolled',
            'rccontinue' : rccontinue,
        }
        request = api.Request(site=SITE, parameters=params)
        data = request.submit()

        for revision in data.get('query', {}).get('recentchanges', []):
            qid = revision.get('title')

            if qid is None:
                continue

            item_text = check_item(qid)
            if item_text is None:
                continue

            if new_date_added is False:
                new_text += f'==={date2}===\n'
                new_date_added = True

            new_text += item_text

        if 'query-continue' in data:
            rccontinue = data.get('query-continue', {}).get('recentchanges', {}).get('rccontinue', 0)
            continue

        break

    return new_text


def main() -> None:
    page = pwb.Page(SITE, 'User:Pasleim/notability')

    new_text = 'The following items may not be notable according to [[WD:N]]. Feel free to remove false positives from the list.\n\n'

    #scan old items
    old_text = page.get()
    new_text += purge_report_page(old_text)

    #check items from yesterday
    new_text += check_items_from_yesterday()

    page.text = new_text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
