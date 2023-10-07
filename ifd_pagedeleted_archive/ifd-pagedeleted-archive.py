#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import re

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()


def count_external_ids(claims:list[pwb.Claim]) -> int:
    cnt = 0
    for pid in claims:
        if claims[pid][0].type=='external-id':
           cnt += 1

    return cnt


def old_edits(page_title:str) -> None:
    text = """{{User:Pasleim/Items for deletion/archivebox-pagedeleted}}
The following items may no longer be notable according to [[WD:N]]. Feel free to remove false positives from the list.

{| class="wikitable sortable plainlinks"
|-
! Item !! # Claims<br /><small>(# sources)</small> !! # Backlinks !! # ext-Id !! Last deleted page !! Timestamp
"""

    page = pwb.Page(SITE, page_title) 
    oldtext = page.get()

    for line in oldtext.split('\n'):
        res = re.search(r'{{Q\|(Q[0-9]+)}} (.*) \|\| (.*) \|\| ([0-9]+) \|\| ([0-9]+) \|\| (.*)', line)
        if not res:
            continue

        qid = res.group(1)
        item = pwb.ItemPage(REPO, qid)

        if not item.exists():
            continue

        if item.isRedirectPage():
            continue

        dict = item.get()
        if len(dict['sitelinks']) > 0:
            continue

        nstat = len(dict['claims'])
        nsources = 0
        for pid in dict['claims']:
            for claim in dict['claims'][pid]:
                for sources_str in claim.getSources():
                    keys = list(sources_str.keys())
                    nsources += len(keys) - keys.count('P143')

        sources_str = '' if nsources == 0 else f' <small>({nsources})</small>'
        backlinks = sum(1 for _ in item.backlinks(namespaces=0))
        external_ids = count_external_ids(dict['claims'])

        text += f"""|-
| {{{{Q|{qid}}}}} {res.group(2)} || {nstat}{sources_str} || {backlinks} || {external_ids} || {res.group(6)}
"""

    text += '|}'

    page.text = text
    page.save(summary='upd', minor=False)


def main() -> None:
    payload = {
        'action': 'query',
        'list': 'allpages',
        'apprefix': 'Pasleim/Items for deletion/Page deleted',
        'aplimit': '120',
        'apnamespace': '2',
        'format': 'json'
    }
    response = requests.get(
        url='https://www.wikidata.org/w/api.php',
        params=payload
    )
    data = response.json()

    for page in data.get('query', {}).get('allpages', []):
        page_title = page.get('title')
        if page_title is None:
            continue

        old_edits(page_title)


if __name__=='__main__':
    main()
