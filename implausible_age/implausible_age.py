# -*- coding: utf-8  -*-

from time import strftime
from typing import Generator

import requests
import pywikibot as pwb


SITE = pwb.Site('wikidata','wikidata')
REPO = SITE.data_repository()

HEADER = """== Implausbible Age ==
List of all person who do not have an age between 0 and 130. Update: <onlyinclude>{update_timestamp}</onlyinclude>

{{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"
|- style="white-space:nowrap;"
! Item !! Birth !! Death !! Age
"""
FOOTER = '|}'
TABLE_ROW = """|-
| {{{{Q|{qid}}}}} || {dob_year}-{dob_month:02d}-{dob_day:02d} || {dod_year}-{dod_month:02d}-{dod_day:02d} || {age}
"""


def query_wdqs(query) -> Generator[str, None, None] :
    response = requests.get(
        'https://query.wikidata.org/bigdata/namespace/wdq/sparql',
        params= {
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': f'{requests.utils.default_user_agent()} (duplicate_arts.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
        }
    )

    payload = response.json()
    for row in payload.get('results', {}).get('bindings', []):
        qid = row.get('entity', {}).get('value', '')[len('http://www.wikidata.org/entity/'):]
        yield qid


def calculate_age(dob_year:int, dob_month:int, dob_day:int, dod_year:int, dod_month:int, dod_day:int) -> int:
    if dod_month<dob_month:
        return dod_year-dob_year-1

    if dob_month==dod_month and dod_day<dob_day:
        return dod_year-dob_year-1

    return dod_year-dob_year


def add_row(qid:str) -> str:
    item = pwb.ItemPage(REPO, qid)
    dict = item.get()
    for dob_claim in dict['claims'].get('P569', []):
        if dob_claim.getTarget().precision < 9:  # 9 = year
            continue
        if dob_claim.rank=='deprecated':
            continue

        for dod_claim in dict['claims'].get('P570', []):
            if dod_claim.getTarget().precision < 9:
                continue
            if dod_claim.rank=='deprecated':
                continue

            age = calculate_age(
                dob_claim.getTarget().year,
                dob_claim.getTarget().month,
                dob_claim.getTarget().day,
                dod_claim.getTarget().year,
                dod_claim.getTarget().month,
                dod_claim.getTarget().day
            )

            if age < 0 or age > 130:
                return TABLE_ROW.format(
                    qid=qid,
                    dob_year=dob_claim.getTarget().year,
                    dob_month=dob_claim.getTarget().month,
                    dob_day=dob_claim.getTarget().day,
                    dod_year=dod_claim.getTarget().year,
                    dod_month=dod_claim.getTarget().month,
                    dod_day=dod_claim.getTarget().day,
                    age=age,
                )

    raise RuntimeWarning(f'Cannot find an implausible age in item {qid}')


def make_report() -> str:
    queries = [  # including precision times out
        'SELECT DISTINCT ?entity WHERE {?entity wdt:P31 wd:Q5; wdt:P569 ?dob; wdt:P570 ?dod . FILTER (year(?dod) - year(?dob) > 130) } ORDER BY ?entity', # check if death date is 130 bigger than birth date
        'SELECT DISTINCT ?entity WHERE {?entity wdt:P31 wd:Q5; wdt:P569 ?dob; wdt:P570 ?dod . FILTER (year(?dod) < year(?dob)) } ORDER BY ?entity',  # check if birth date is smaller than death date
    ]

    text = ''
    for query in queries:
        for qid in query_wdqs(query):
            try:
                text += add_row(qid)
            except RuntimeWarning as exception:
                print(exception)

    return text


def main() -> None:
    text = HEADER.format(update_timestamp=strftime('%H:%M, %d %B %Y (%Z)')) + make_report() + FOOTER
    
    page = pwb.Page(SITE, 'User:Pasleim/Implausible/age')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
