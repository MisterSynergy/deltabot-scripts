#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from time import sleep, strftime
from typing import Any

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

HEADER = """A list of the most linked {specifier} items. Data as of <onlyinclude>{timestamp}</onlyinclude>.

"""

TABLE_HEADER = """{| class="wikitable sortable" style="width:100%; margin:auto;"
|-
! Item !! Usage
"""

TABLE_ROW = """|-
| {{{{Q|{qid}}}}} || {cnt}
"""

TABLE_FOOTER = """|}

"""

FOOTER = """[[Category:Wikidata statistics]]"""


WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT =f'{requests.utils.default_user_agent()} (popular_pages.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WDQS_SLICING_LIMIT = 250_000
WD = 'http://www.wikidata.org/entity/'

SMALL_NUMBERS_CUTOFF = 50
SMALL_NUMBERS_LIMIT = 10


def query_wdqs(query:str, retry_credit:int=3) -> list[dict[str, dict[str, Any]]]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
            'query' : query,
        },
        headers={
            'User-Agent' : WDQS_USER_AGENT,
            'Accept' : 'application/sparql-results+json',
        }
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        if response.status_code == 500 and ('offset is out of range' in response.text):  # slice service depleted
            return []

        if response.status_code == 500 and ('fromIndex > toIndex' in response.text):  # slice service depleted at first slice
            return []

        if response.status_code == 429 and retry_credit > 0:  # we are likely running too fast; try up to three times
            sleep(120)
            return query_wdqs(query, retry_credit-1)

        raise RuntimeError(f'Cannot parse WDQS endpoint response body as JSON for query "{query}"; HTTP status: {response.status_code}; query time: {response.elapsed.total_seconds():.2f} sec') from exception

    return payload.get('results', {}).get('bindings', [])


def query_backlinks(wd_class:str) -> dict[str, int]:
    query_template = """SELECT ?item (COUNT(?backlink) AS ?cnt) WHERE {{
  SERVICE bd:slice {{
    ?item wdt:P31 wd:{wd_class} .
    bd:serviceParam bd:slice.offset {offset} .
    bd:serviceParam bd:slice.limit {limit} .
  }}
  ?backlink ?p ?item .
  FILTER(?p NOT IN (schema:about, owl:sameAs)) .
  FILTER NOT EXISTS {{ [] wikibase:directClaim ?p }}
}} GROUP BY ?item ORDER BY DESC(?cnt)"""

    offset = 0
    limit = WDQS_SLICING_LIMIT

    qids = {}

    while True:
        #print(strftime("%H:%M:%S"), wd_class, offset, limit)
        query = query_template.format(
            offset=offset,
            limit=limit,
            wd_class=wd_class,
        )
        chunk = query_wdqs(query)

        if len(chunk) == 0:
            break

        for row in chunk:
            qid = row.get('item', {}).get('value', '').replace(WD, '')
            cnt_str = row.get('cnt', {}).get('value')

            if qid == '' or cnt_str is None:
                continue

            cnt = int(cnt_str)

            if qid not in qids:
                qids[qid] = cnt
            else:
                qids[qid] += cnt

        offset += limit

    if len(qids) == 0:
        return qids

    if max(qids.values()) >= SMALL_NUMBERS_CUTOFF:
        chunked_qids = { qid : cnt for qid, cnt in qids.items() if cnt >= SMALL_NUMBERS_CUTOFF }
        chunked_qids_sorted = dict(sorted(chunked_qids.items(), key=lambda x:x[1], reverse=True))
    else:
        qids_sorted = dict(sorted(qids.items(), key=lambda x:x[1], reverse=True))
        chunked_qids_sorted = { qid : qids_sorted[qid] for qid in list(qids_sorted)[:SMALL_NUMBERS_LIMIT] }  # small numbers anyways, max SMALL_NUMBERS_LIMIT elements

    return chunked_qids_sorted


def query_type_items(root_class:str) -> dict[str, str]:
    query = f"""PREFIX gas: <http://www.bigdata.com/rdf/gas#>
SELECT DISTINCT ?item ?itemLabel (xsd:integer(?depth_float) AS ?depth) WHERE {{
  SERVICE gas:service {{
    gas:program gas:gasClass 'com.bigdata.rdf.graph.analytics.SSSP';
                gas:in wd:{root_class};
                gas:linkType wdt:P279;
                gas:traversalDirection 'Reverse';
                gas:maxIterations 6;
                gas:out ?item;
                gas:out1 ?depth_float .
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en' }}
}} ORDER BY ASC(?depth) ASC(STRAFTER(STR(?item), STR(wd:)))"""

    qids = {}
    for row in query_wdqs(query):
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        label = row.get('itemLabel', {}).get('value', '')

        qids[qid] = label

    return qids


def make_report(root_class:str) -> str:
    type_qids = query_type_items(root_class)
    text = ''

    for type_qid, label in type_qids.items():
        backlinks = query_backlinks(type_qid)
        if len(backlinks) == 0:
            continue

        text += f'== Type "{label}" ([[{type_qid}]]) ==\n{TABLE_HEADER}'
        for qid, cnt in backlinks.items():
            item_page = pwb.ItemPage(REPO, qid)
            item_page.get()

            if not item_page.exists():
                continue
            if item_page.isRedirectPage():
                continue
            if not item_page.claims:
                continue

            for claim in item_page.claims.get('P31', []):
                if claim.getSnakType()!='value':
                    continue
                if claim.getTarget().getID()==type_qid:
                    text += TABLE_ROW.format(qid=qid, cnt=cnt)
                    break

        text += f'{TABLE_FOOTER}'

    return text


def report_dab_pages() -> None:
    text = HEADER.format(specifier='disambiguation page', timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report('Q4167410') + FOOTER
    save_to_wiki('Wikidata:Database reports/Most linked disambiguation page items', text)


def report_category_pages() -> None:
    text = HEADER.format(specifier='category page', timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report('Q4167836') + FOOTER
    save_to_wiki('Wikidata:Database reports/Most linked category items', text)


def save_to_wiki(page_title:str, text:str) -> None:
    page = pwb.Page(SITE, page_title)
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)

    #with open(f'/data/project/deltabot/{page_title.replace("Wikidata:Database reports/", "").replace(" ", "_")}.txt', mode='w', encoding='utf8') as file_handle:
    #    file_handle.write(text)


def main():
    report_dab_pages()
    report_category_pages()


if __name__=='__main__':
    main()
