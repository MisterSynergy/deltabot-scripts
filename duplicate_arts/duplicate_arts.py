#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from typing import Generator

import pywikibot as pwb
import requests


WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT = f'{requests.utils.default_user_agent()} (duplicate_arts.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'


def query_wdqs(query:str) -> Generator[tuple[str, str], None, None]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent' : WDQS_USER_AGENT,
        }
    )

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse WDQS response as JSON; HTTP status {response.status_code}; response time {response.elapsed.total_seconds():.2f} sec') from exception

    for row in data.get('results', {}).get('bindings', []):
        item1 = row.get('item1', {}).get('value', '').replace(WD, '')
        item2 = row.get('item2', {}).get('value', '').replace(WD, '')

        yield item1, item2


def candidate_by_image() -> str:
    query = """SELECT DISTINCT ?item1 ?item2 WHERE {
  ?item1 wdt:P31/wdt:P279* wd:Q3305213; wdt:P18 ?image . 
  ?item2 wdt:P31/wdt:P279* wd:Q3305213; wdt:P18 ?image . 
  FILTER(STR(?item1) < STR(?item2)) .
} ORDER BY ASC(xsd:integer(STRAFTER(STR(?item1), 'entity/Q')))"""

    text = ''
    for item, item2 in query_wdqs(query):
        text += f'* {{{{Q|{item}}}}}, {{{{Q|{item2}}}}}\n'

    return text


def candidate_by_qualifier(ps:str, pq:str) -> str:
    query = f"""SELECT DISTINCT ?item1 ?item2 WHERE {{
  ?item1 wdt:P31/wdt:P279* wd:Q3305213 .   
  ?item1 p:{ps} ?statement1 .
  ?statement1 ps:{ps} ?value; pq:{pq} ?qvalue .

  ?item2 wdt:P31/wdt:P279* wd:Q3305213 .   
  ?item2 p:{ps} ?statement2 .
  ?statement2 ps:{ps} ?value; pq:{pq} ?qvalue .

  FILTER(STR(?item1) < STR(?item2)) .
}} ORDER BY STR(?item1) LIMIT 500"""

    text = ''
    for item1, item2 in query_wdqs(query):
        text += f'* {{{{Q|{item1}}}}}, {{{{Q|{item2}}}}}\n'

    return text


def main() -> None:
    try:
        text_by_qualifier_1 = candidate_by_qualifier('P217', 'P195')
    except RuntimeError as exception:
        text_by_qualifier_1 = f"''(query error: {exception})''"
    try:
        text_by_qualifier_2 = candidate_by_qualifier('P528', 'P972')
    except RuntimeError as exception:
        text_by_qualifier_2 = f"''(query error: {exception})''"
    try:
        text_by_image = candidate_by_image()
    except RuntimeError as exception:
        text_by_image = f"''(query error: {exception})''"

    text = f"""__TOC__
== Items with same inventory number of the same collection ==
{text_by_qualifier_1}

== Items with same catalog code of the same catalog ==
{text_by_qualifier_2}

== Paintings with same image ==
{text_by_image}

[[Category:WikiProject sum of all paintings|Duplicate paintings]]
[[Category:Database reports|Duplicate paintings]]
[[Category:Merge candidates|Duplicate paintings]]"""

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:WikiProject sum of all paintings/Duplicate paintings')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__ == '__main__':
    main()
