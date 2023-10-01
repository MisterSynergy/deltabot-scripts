# -*- coding: utf-8  -*-

from json.decoder import JSONDecodeError
from time import strftime
from typing import Any

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


def query_wdqs_chunk(query:str) -> list[dict[str, Any]]:
    response = requests.post(
        url='https://query.wikidata.org/bigdata/namespace/wdq/sparql',
        data={
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': f'{requests.utils.default_user_agent()} (implausible_age.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)',
        }
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        if 'offset is out of range' in response.text:
            return []

        raise RuntimeWarning('Cannot parse WDQS response as JSON') from exception

    return payload.get('results', {}).get('bindings', [])


def query_wdqs_chunked(query_part:str) -> list[str]:
    query_template = """SELECT DISTINCT ?item WITH {{
  SELECT ?item WHERE {{
    SERVICE bd:slice {{
      ?item wdt:P31 wd:Q5 .
      bd:serviceParam bd:slice.offset {offset} .
      bd:serviceParam bd:slice.limit {limit} .
    }}
  }}
}} AS %subquery WHERE {{
  INCLUDE %subquery .

  {query_part}
}}"""

    offset = 0
    limit = 500_000

    qids = []

    while True:
        query = query_template.format(
            offset=offset,
            limit=limit,
            query_part=query_part,
        )

        try:
            chunk = query_wdqs_chunk(query)
        except RuntimeWarning as exception:
            print(f'Failed to query {limit} sets from offset {offset}; exception: {exception}; query: {query}')
            offset += limit
            continue

        if len(chunk) == 0:
            break

        for row in chunk:
            qid = row.get('item', {}).get('value', '')[len('http://www.wikidata.org/entity/'):]
            qids.append(qid)

        offset += limit

    return qids


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
        if dob_claim.getSnakType() != 'value':
            continue
        if dob_claim.getTarget().precision < 9:  # 9 = year
            continue
        if dob_claim.rank=='deprecated':
            continue

        for dod_claim in dict['claims'].get('P570', []):
            if dod_claim.getSnakType() != 'value':
                continue
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
    query_fragment = """  ?item p:P570 [ psv:P570 [ wikibase:timeValue ?dod; wikibase:timePrecision ?dod_precision ]; wikibase:rank ?dod_rank ].
  FILTER(?dod_precision >= 9) .
  FILTER(?dod_rank != wikibase:DeprecatedRank) .

  ?item p:P569 [ psv:P569 [ wikibase:timeValue ?dob; wikibase:timePrecision ?dob_precision ]; wikibase:rank ?dob_rank ] .
  FILTER(?dob_precision >= 9) .
  FILTER(?dob_rank != wikibase:DeprecatedRank) .

  """

    query_parts = [  # including precision times out
        f"""{query_fragment}FILTER(YEAR(?dod) - YEAR(?dob) > 130) .""", # check if death date is 130 bigger than birth date
        f"""{query_fragment}FILTER(YEAR(?dod) < YEAR(?dob)) .""",  # check if birth year is smaller than death year
    ]

    text = ''
    for query_part in query_parts:
        for qid in query_wdqs_chunked(query_part):
            try:
                text += add_row(qid)
            except RuntimeWarning as exception:
                print(exception)

    return text


def main() -> None:
    try:
        report = make_report()
    except RuntimeError as exception:
        print(exception)
    else:
        if len(report) > 0:
            text = HEADER.format(update_timestamp=strftime('%H:%M, %d %B %Y (%Z)')) + report + FOOTER

            page = pwb.Page(SITE, 'User:Pasleim/Implausible/age')
            page.text = text
            page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
