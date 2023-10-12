#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from time import strftime
from typing import Any

import pywikibot as pwb
import requests


# cf. https://www.wikidata.org/w/api.php?action=wbavailablebadges for available badges
BADGES = [
    'Q17437796',  # featured article badge
    'Q17437798',  # good article badge
    'Q17506997',  # featured list badge
    'Q17559452',  # recommended article
    'Q17580674',  # featured portal badge
#   'Q20748091',  # not proofread (Wikisource only)
#   'Q20748092',  # proofread (Wikisource only)
#   'Q20748093',  # validated (Wikisource only)
#   'Q20748094',  # problematic (Wikisource only)
#   'Q28064618',  # digital document (Wikisource only)
    'Q51759403',  # good list badge
#   'Q70893996',  # sitelink to redirect
#   'Q70894304',  # intentional sitelink to redirect
]

WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT = f'{requests.utils.default_user_agent()} (badge_statistics.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'
HEADER = """Update: <onlyinclude>{update_timestamp}</onlyinclude>

"""
FOOTER = """|}

[[Category:Wikidata statistics|Badge statistics]]"""


def query_wdqs(query:str) -> list[dict[str, Any]]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent' : WDQS_USER_AGENT,
        },
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse WDQS response as JSON; status code {response.status_code}; time {response.elapsed.total_seconds():.2f} sec; query: {query}') from exception

    return payload.get('results', {}).get('bindings', [])


def create_single_ranking(badge:str) -> str:
    text  = f"""== Top 20: {{{{Q|{badge}}}}} ==

{{| class="wikitable sortable"
! Item !! {{{{Q|{badge}}}}}
"""
    query = f"""SELECT ?item (COUNT(*) AS ?cnt) WHERE {{
        ?article schema:about ?item; wikibase:badge wd:{badge} .
    }} GROUP BY ?item ORDER BY DESC(?cnt) LIMIT 20"""

    for row in query_wdqs(query):
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        cnt = row.get('cnt', {}).get('value')
        if len(qid)==0 or cnt is None:
            continue

        text += f"""|-
| {{{{Q|{qid}}}}} || {cnt}
"""

    text += """|}

"""

    return text


def create_total_ranking(badges:list[str]) -> str:
    text  = f"""== Top 50: Overall ==

{{| class="wikitable sortable"
! Item {''.join([ f'!! {{{{Q|{badge}}}}} ' for badge in badges ] )}!! total
"""

    query = f"""SELECT ?item (GROUP_CONCAT(?badge; SEPARATOR=',') AS ?badges) (GROUP_CONCAT(?cnt; SEPARATOR=',') AS ?counts) (SUM(?cnt) AS ?sum) WHERE {{
        {{
            SELECT ?item ?badge (COUNT(*) AS ?cnt) WHERE {{
                VALUES ?badge {{ wd:{' wd:'.join(badges)} }}
                ?article schema:about ?item; wikibase:badge ?badge .
            }} GROUP BY ?item ?badge
        }}
    }} GROUP BY ?item ORDER BY DESC(?sum) LIMIT 50"""

    collec = []
    for row in query_wdqs(query):
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        sitelink_badges = row.get('badges', {}).get('value', '').split(',')
        counts = row.get('counts', {}).get('value', '').split(',')
        total_sum = row.get('sum', {}).get('value')

        if qid=='' or len(sitelink_badges)==0 or len(counts)==0 or len(sitelink_badges)!=len(counts) or total_sum is None:
            continue

        item = {
            'qid' : qid,
            'sum' : total_sum,
            'badge_counts' : {},
        }

        for badge, count in zip(sitelink_badges, counts):
            item['badge_counts'][badge.replace(WD, '')] = count

        collec.append(item)

    for item in collec:
        text += f"""|-
| {{{{Q|{item['qid']}}}}} || { ''.join([f'{item.get("badge_counts", {}).get(badge, "")} || ' for badge in badges ])} {item.get('sum', '')}
"""

    return text


def main() -> None:
    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)'))

    try:
        for badge in BADGES:
            text += create_single_ranking(badge)
        text += create_total_ranking(BADGES)
    except RuntimeError as exception:
        print(exception)
        return

    text += FOOTER

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Badge statistics')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
