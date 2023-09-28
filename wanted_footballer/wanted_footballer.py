#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from time import strftime
from typing import Generator

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata','wikidata')

PROJECTS = ['en','sv','nl','de','fr','war','ceb','ru','it','es','vi','pl','ja','pt','zh','uk','ca','fa','no','fi','id','ar','sr','cs','ko','sh','hu','ms','ro','tr']

WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USERAGENT = f'{requests.utils.default_user_agent()} (wanted_footballer.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'


def query_wdqs(query:str) -> Generator[dict, None, None]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
            'query' : query,
            'format' : 'json',
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': WDQS_USERAGENT,
        }
    )

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as exception:
        raise RuntimeError('Cannot parse result from SPARQL endpoint') from exception

    for row in data.get('results', {}).get('bindings', []):
        yield row


def make_report(project:str) -> None:
    text = f'Many wikipedia have these articles. Please create these articles in [[:{project}:|{project} wikipedia]]. Update: <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>\n'
    cnt = 0

    query = f"""SELECT ?item ?cnt WHERE {{
    {{
        SELECT ?item (COUNT(*) AS ?cnt) WHERE {{
            ?item wdt:P106 wd:Q937857; ^schema:about ?article
        }} GROUP BY ?item ORDER BY DESC(?cnt)
    }}
    FILTER NOT EXISTS {{ ?item ^schema:about/schema:isPartOf <https://{project}.wikipedia.org/> }}
}} ORDER BY DESC(?cnt) LIMIT 100"""

    try:
        result = query_wdqs(query)
    except RuntimeError:
        return  # skip project

    for row in result:
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        
        if row.get('cnt', {}).get('value', 0) != cnt:
            cnt = row.get('cnt', {}).get('value', 0)
            text += f'\n== {cnt} wikipedia ==\n'
        text += f'*{{{{Q|{qid}}}}}\n'
    text += '\n[[Category:WikiProject Association football/Wanted footballers]]'

    #write to wikidata
    page = pwb.Page(SITE, f'Wikidata:WikiProject Association football/Wanted footballers/{project}')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


def main():
    for project in PROJECTS:
        make_report(project)


if __name__ == '__main__':
    main()
