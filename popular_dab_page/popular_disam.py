#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from time import sleep, strftime
from typing import Any

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata','wikidata')
REPO = SITE.data_repository()

HEADER = f"""A list of the most linked disambiguation page items. Data as of <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>.

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
WDQS_USER_AGENT =f'{requests.utils.default_user_agent()} (popular_disam.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'


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
    limit = 250_000

    qids = {}

    while True:
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

    if max(qids.values()) >= 50:
        chunked_qids = { qid : cnt for qid, cnt in qids.items() if cnt >= 50 }
        chunked_qids_sorted = dict(sorted(chunked_qids.items(), key=lambda x:x[1], reverse=True))
    else:
        qids_sorted = dict(sorted(qids.items(), key=lambda x:x[1], reverse=True))
        chunked_qids_sorted = { qid : qids_sorted[qid] for qid in list(qids_sorted)[:10] }  # small numbers anyways, max 10 elements

    return chunked_qids_sorted


def query_dab_classes() -> dict[str, str]:
    query = """PREFIX gas: <http://www.bigdata.com/rdf/gas#>

SELECT DISTINCT ?item ?itemLabel (xsd:integer(?depth_float) AS ?depth) WHERE {
  SERVICE gas:service {
    gas:program gas:gasClass 'com.bigdata.rdf.graph.analytics.SSSP';
                gas:in wd:Q4167410;
                gas:linkType wdt:P279;
                gas:traversalDirection 'Reverse';
                gas:maxIterations 4;
                gas:out ?item;
                gas:out1 ?depth_float .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language 'en' }
} ORDER BY ASC(?depth) ASC(STRAFTER(STR(?item), STR(wd:)))"""

    query_result = query_wdqs(query)
    dab_qids = {}
    for row in query_result:
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        label = row.get('itemLabel', {}).get('value', '')
        dab_qids[qid] = label

    return dab_qids


def make_report() -> str:
    dab_qids = query_dab_classes()
    text = ''

    for dab_qid, label in dab_qids.items():
        text += f'== Type "{label}" ([[{dab_qid}]]) ==\n{TABLE_HEADER}'

        backlinks = query_backlinks(dab_qid)
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
                if claim.getTarget().getID()==dab_qid:
                    text += TABLE_ROW.format(qid=qid, cnt=cnt)

        text += f'{TABLE_FOOTER}'

    return text


def main():
    text = HEADER + make_report() + FOOTER

    page = pwb.Page(SITE, 'Wikidata:Database reports/Most linked disambiguation page items')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
