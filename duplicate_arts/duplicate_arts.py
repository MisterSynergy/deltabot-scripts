#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from typing import Generator

import pywikibot as pwb
import requests


def query_wdqs(query:str) -> Generator[tuple[str, str], None, None]:
    response = requests.get(
        url='https://query.wikidata.org/bigdata/namespace/wdq/sparql',
        params={
            query : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': f'{requests.utils.default_user_agent()} (duplicate_arts.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
        }
    )

    data = response.json()

    for row in data.get('results', {}).get('bindings', []):
        item = row.get('item', {}).get('value', '').replace('http://www.wikidata.org/entity/', '')
        item2 = row.get('item2', {}).get('value', '').replace('http://www.wikidata.org/entity/', '')

        yield item, item2


def candidate_by_image() -> str:
    query = """SELECT DISTINCT ?item ?item2 WHERE {
  ?item wdt:P31/wdt:P279* wd:Q3305213 . 
  ?item2 wdt:P31/wdt:P279* wd:Q3305213 . 
  ?item wdt:P18 ?image .
  ?item2 wdt:P18 ?image .
  FILTER(?item != ?item2 && str(?item) < str(?item2)) .
} ORDER BY str(?item) LIMIT 500"""

    text = ''
    for item, item2 in query_wdqs(query):
        text += f'* {{{{Q|{item}}}}}, {{{{Q|{item2}}}}}\n'

    return text


def candidate_by_qualifier(ps:str, pq:str) -> str:
    query = f"""SELECT DISTINCT ?item1 ?item2 WHERE {{
  ?item1 wdt:P31/wdt:P279* wd:Q3305213 .   
  ?item1 p:{ps} ?statement1 .
  ?statement1 ps:{ps} ?value; pq:{pq} ?qvalue1 .

  ?item2 wdt:P31/wdt:P279* wd:Q3305213 .   
  ?item2 p:{ps} ?statement2 .
  ?statement2 ps:{ps} ?value; pq:{pq} ?qvalue2 .

  FILTER(STR(?item1) < STR(?item2)) .
  FILTER(?qvalue1 = ?qvalue2) .
}} ORDER BY STR(?item1) LIMIT 500"""

    text = ''
    for item1, item2 in query_wdqs(query):
        text += f'*{{{{Q|{item1}}}}}, {{{{Q|{item2}}}}}\n'

    return text


def main() -> None:
    text = f"""__TOC__
== Items with same inventory number of the same collection ==
{candidate_by_qualifier('P217', 'P195')}

== Items with same catalog code of the same catalog ==
{candidate_by_qualifier('P528', 'P972')}

== Paintings with same image ==
{candidate_by_image()}

[[Category:WikiProject sum of all paintings|Duplicate paintings]]
[[Category:Database reports|Duplicate paintings]]
[[Category:Merge candidates|Duplicate paintings]]"""

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:WikiProject sum of all paintings/Duplicate paintings')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__ == '__main__':
    main()
