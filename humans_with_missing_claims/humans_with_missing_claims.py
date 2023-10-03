#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
import re
from time import strftime
from typing import Any

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')
MISSING_PROPERTIES = [ 'P21', 'P19', 'P569', 'P734', 'P735' ]
USER_AGENT = f'{requests.utils.default_user_agent()} (humans_with_missing_claims.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'


def query_wdqs(query:str) -> list[dict[str, Any]]:
    response = requests.post(
        url='https://query.wikidata.org/bigdata/namespace/wdq/sparql',
        data={
            'query' : query,
        },
        timeout=65,
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent' : USER_AGENT,
        }
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        raise RuntimeWarning('Cannot parse JSON response') from exception

    return payload.get('results', {}).get('bindings', [])
    

def create_summary(counts:dict[str, dict[str, int]]) -> None:
    props = list(counts.keys())
    props.sort(key=lambda x: int(x[1:]))

    text = f'Update: <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>\n\n{{| class="wikitable sortable"\n! Id !! Property '

    for p2 in MISSING_PROPERTIES:
        text += f'!! {{{{P|{p2}}}}} '

    for p1 in props:
        text += f'\n|-\n|data-sort-value={p1[1:]}| [[Property:{p1}|{p1}]] || [[/{p1}|{{{{label|{p1}}}}}]]'

        for p2 in MISSING_PROPERTIES:
            if p2 in counts[p1]:
                text += f' || [[/{p1}#{p2}|{counts[p1][p2]}]]'
            else:
                text += ' || -'

    text += '\n|}\n\nNew reports can be requested on [[/input]].\n[[Category:Database reports]]'

    page = pwb.Page(SITE, 'Wikidata:Database reports/Humans with missing claims')
    page.text = text
    page.save(summary='upd', minor=False)


def create_report(p1:str, results:dict[str, list[str]], counts:dict[str, int]) -> None:
    cnt = 0
    text = ''

    for p2 in MISSING_PROPERTIES:
        cnt_p2 = counts.get(p2)
        if cnt_p2 is None:
            continue
        
        text += f'== <span id="{p2}"></span> Missing {{{{P|{p2}}}}} ==\n'
        text += f'count: {cnt_p2}\n\n'

        for qid in results[p2]:
            cnt += 1
            if cnt < 2500:
                text += f'*{{{{Q|{qid}}}}}\n'
            else:
                text += f'*[[{qid}]]\n'

        if cnt_p2 > 1000:
            skip = cnt_p2-1000
            text += f'{skip} records skipped\n'

    if len(text)==0:
        return

    text +='__FORCETOC__'

    page = pwb.Page(SITE, f'Wikidata:Database reports/Humans with missing claims/{p1}')
    page.text = text
    page.save(summary=f'report update for [[Property:{p1}]]', minor=False)


def create_lists(properties:list[str]) -> None:
    sparql = """SELECT ?item WHERE {{
    ?item wdt:{p1} [] .
    ?item wdt:P31 wd:Q5 .
    OPTIONAL {{
        ?item wdt:{p2} ?missing .
    }}
    FILTER(!BOUND(?missing)) .
}} ORDER BY ?item LIMIT 1000"""

    sparql_count = """SELECT (COUNT(DISTINCT ?item) AS ?cnt) WHERE {{
    ?item wdt:{p1} [] .
    ?item wdt:P31 wd:Q5 .
    OPTIONAL {{
        ?item wdt:{p2} ?missing .
    }}
    FILTER(!BOUND(?missing)) .
}}"""

    counts:dict[str, dict[str, int]] = {}
    for p1 in properties:
        results:dict[str, list[str]] = {}
        counts[p1] = {}
        for p2 in MISSING_PROPERTIES:
            results[p2] = []
            
            payload_1 = query_wdqs(sparql.format(p1=p1, p2=p2))
            payload_2 = query_wdqs(sparql_count.format(p1=p1, p2=p2))

            for row in payload_1:
                qid = row.get('item', {}).get('value', '')[len('http://www.wikidata.org/entity/'):]
                results[p2].append(qid)

            counts[p1][p2] = int(payload_2[0].get('cnt', {}).get('value', '0'))

        if len(counts[p1]) > 0:
            create_report(p1, results, counts[p1])

    create_summary(counts)


def read_input() -> list[str]:
    page = pwb.Page(SITE, 'Wikidata:Database reports/Humans with missing claims/input')
    text = page.get()
    lines = text.split('\n')

    return lines


def main() -> None:
    lines = read_input()

    properties:list[str] = []
    for line in lines:
        if line.startswith('#'):
            continue

        if re.match('^P\d+$', line) is None:
            continue

        properties.append(line)

    create_lists(properties)


if __name__=='__main__':
    main()
