#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from collections.abc import Generator
from json import JSONDecodeError
from time import sleep, strftime
from typing import Any

import pywikibot as pwb
import requests
from requests.utils import default_user_agent


SITE = pwb.Site('wikidata', 'wikidata')

WDQS_ENDPOINTS = [
    'https://query.wikidata.org/sparql',
    'https://query-scholarly.wikidata.org/sparql',
]
WDQS_USER_AGENT =f'{default_user_agent()} (property_uses.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WDQS_SLEEP = 2  # seconds between requests, in order to avoid being blocked at the endpoint
WD = 'http://www.wikidata.org/entity/'

# credits to User:Infrastruktur for assembling this query
QUERY_MAINGRAPH = """# Property uses. Caveat emptor: Completely relies on finicky non-portable Blazegraph optimization.
SELECT ?prop (SAMPLE(?claim_) AS ?claim) (SAMPLE(?qualifier_) AS ?qualifier) (SAMPLE(?reference_) AS ?reference) WITH {
  SELECT ?p (COUNT(?s) AS ?count) WHERE {
    ?s ?p ?o
  } GROUP BY ?p
} AS %subquery WHERE {
  { 
    SELECT ?prop (?count AS ?claim_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      ?prop wikibase:claim ?p .
    }
  } UNION {
    SELECT ?prop (?count AS ?qualifier_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      ?prop wikibase:qualifier ?p .
    }
  } UNION {
    SELECT ?prop (?count AS ?reference_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      ?prop wikibase:reference ?p .
    }
  }
} GROUP BY ?prop"""

QUERY_SUBGRAPH = """# Property uses. Caveat emptor: Completely relies on finicky non-portable Blazegraph optimization.
SELECT ?prop (SAMPLE(?claim_) AS ?claim) (SAMPLE(?qualifier_) AS ?qualifier) (SAMPLE(?reference_) AS ?reference) WITH {
  SELECT ?p (COUNT(?s) AS ?count) WHERE {
    ?s ?p ?o
  } GROUP BY ?p
} AS %subquery WHERE {
  { 
    SELECT ?prop (?count AS ?claim_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      SERVICE <https://query.wikidata.org/sparql> {
        ?prop wikibase:claim ?p .
      }
    }
  }
  UNION
  {
    SELECT ?prop (?count AS ?qualifier_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      SERVICE <https://query.wikidata.org/sparql> {
        ?prop wikibase:qualifier ?p .
      }
    }
  }
  UNION
  {
    SELECT ?prop (?count AS ?reference_) WHERE {
      hint:SubQuery hint:optimizer 'None'.
      INCLUDE %subquery .
      SERVICE <https://query.wikidata.org/sparql> {
        ?prop wikibase:reference ?p .
      }
    }
  }
} GROUP BY ?prop"""


def query_wdqs(wdqs_endpoint:str, query:str) -> Generator[dict[str, Any], None, None]:
    response = requests.post(
        url=wdqs_endpoint,
        data={
            'query' : query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': WDQS_USER_AGENT,
        }
    )

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse WDQS response as JSON; HTTP status {response.status_code}; query time {response.elapsed.total_seconds:.2f} sec') from exception

    for row in data.get('results', {}).get('bindings', []):
        yield row


def collect_data() -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    total:dict[str, int] = {}
    mainsnak:dict[str, int] = {}
    qualifiers:dict[str, int] = {}
    references:dict[str, int] = {}

    for wdqs_endpoint in WDQS_ENDPOINTS:
        if wdqs_endpoint == 'https://query.wikidata.org/sparql':
            query = QUERY_MAINGRAPH
        else:
            query = QUERY_SUBGRAPH

        for row in query_wdqs(wdqs_endpoint, query):
            prop = row.get('prop', {}).get('value', '').replace(WD, '')
            mainsnak_count = int(row.get('claim', {}).get('value', 0))
            qualifier_count = int(row.get('qualifier', {}).get('value', 0))
            reference_count = int(row.get('reference', {}).get('value', 0))

            if prop not in total:
                total[prop] = 0
                mainsnak[prop] = 0
                qualifiers[prop] = 0
                references[prop] = 0

            total[prop] += mainsnak_count
            mainsnak[prop] += mainsnak_count

            total[prop] += qualifier_count
            qualifiers[prop] += qualifier_count

            total[prop] += reference_count
            references[prop] += reference_count

        sleep(WDQS_SLEEP)

    return total, mainsnak, qualifiers, references


def save_to_wiki_page(page_title:str, wikitext:str) -> None:
    page = pwb.Page(SITE, page_title)
    page.text = wikitext
    page.save(summary='upd', minor=False)


def write_report(dct:dict[str, int], page_title:str) -> None:
    wikitext = '<includeonly>{{#switch:{{{1}}}\n'
    keys = list(dct.keys())
    keys.sort(key=lambda x: int(x[1:]))
    for pid in keys:
        wikitext += f'|{pid[1:]}={dct[pid]:d}\n'
    wikitext += '}}</includeonly>\n'
    wikitext += '<noinclude>{{Documentation}}</noinclude>'

    save_to_wiki_page(page_title, wikitext)


# write [[Template:Property uses]]
def write_property_uses_template(dct:dict[str, int]) -> None:
    write_report(dct, 'Template:Property uses')


# write [[Template:Number of main statements by property]]
def write_number_of_main_statements_by_property_template(dct:dict[str, int]) -> None:
    write_report(dct, 'Template:Number of main statements by property')


# write [[Template:Number of qualifiers by property]]
def write_number_of_qualifiers_by_property_template(dct:dict[str, int]) -> None:
    write_report(dct, 'Template:Number of qualifiers by property')


# write [[Template:Number of references by property]]
def write_number_of_references_by_property(dct:dict[str, int]) -> None:
    write_report(dct, 'Template:Number of references by property')


# write [[Wikidata:Database reports/List of properties/Top100]]
def write_top100_database_report(total:dict[str, int]) -> None:
    header = f"""A list of the top 100 [[Help:Properties|properties]] by quantity of item pages that link to them. Data as of <onlyinclude>{strftime("%Y-%m-%d %H:%M (%Z)")}</onlyinclude>.

{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|-
! Property !! Quantity of item pages
"""

    table_row = """|-
| {{{{P|{pid}}}}} || [//wikidata.org/wiki/Special:WhatLinksHere/Property:{pid}?namespace=0 {txt}]
"""

    footer = """|}

[[Category:Properties]]
[[Category:Wikidata statistics]]"""

    sorted_total = sorted(total.items(), key=lambda item: item[1], reverse=True)
    content = ""
    for m in sorted_total[:100]:
        content += table_row.format(pid=m[0], txt=m[1])

    wikitext = header + content + footer

    save_to_wiki_page('Wikidata:Database reports/List of properties/Top100', wikitext)


def main() -> None:
    total, mainsnak, qualifiers, references = collect_data()

    write_property_uses_template(total)
    write_number_of_main_statements_by_property_template(mainsnak)
    write_number_of_qualifiers_by_property_template(qualifiers)
    write_number_of_references_by_property(references)
    write_top100_database_report(total)


if __name__=='__main__':
    main()
