#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json import JSONDecodeError
from time import sleep, strftime

import pywikibot as pwb
import requests
from requests.utils import default_user_agent


SITE = pwb.Site('wikidata', 'wikidata')

LDF_ENDPOINT = 'https://query.wikidata.org/bigdata/ldf'
LDF_USER_AGENT =f'{default_user_agent()} (property_uses.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
LDF_SLEEP = 2  # seconds between requests, in order to avoid being blocked at the endpoint


def query_uses(predicate:str, query_credit:int=3) -> int:
    response = requests.get(
        url=LDF_ENDPOINT,
        params={
            'predicate' : predicate,
        },
        headers={
            'User-Agent' : LDF_USER_AGENT,
            'Accept' : 'application/ld+json',
        }
    )
    sleep(LDF_SLEEP)

    try:
        data = response.json()
    except JSONDecodeError as exception:
        if response.status_code == 429:  # we are likely running too fast
            query_credit -= 1
            if query_credit > 0:
                sleep(120)
                return query_uses(predicate, query_credit)

        raise RuntimeError(f'Cannot parse LDF endpoint response body as JSON for predicate "{predicate}"; HTTP status: {response.status_code}; query time: {response.elapsed.total_seconds():.2f} sec') from exception

    for dct in data.get('@graph', []):
        if 'void:triples' not in dct:
            continue

        return int(dct['void:triples'])

    raise RuntimeError('Not triple count found in JSON response')


def query_mainsnak_uses(prop:str) -> int:
    return query_uses(f'http://www.wikidata.org/prop/{prop}')


def query_qualifier_uses(prop:str) -> int:
    return query_uses(f'http://www.wikidata.org/prop/qualifier/{prop}')


def query_reference_uses(prop:str) -> int:
    return query_uses(f'http://www.wikidata.org/prop/reference/{prop}')


def collect_data() -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    total:dict[str, int] = {}
    mainsnak:dict[str, int] = {}
    qualifiers:dict[str, int] = {}
    references:dict[str, int] = {}

    # collect data
    apcontinue = ''
    while True:
        payload = {
            'action' : 'query',
            'list' : 'allpages',
            'apnamespace' : '120',
            'aplimit' : 'max',
            'apcontinue' : apcontinue,
            'format' : 'json',
        }
        response = requests.get('https://www.wikidata.org/w/api.php', params=payload)
        data = response.json()
        for m in data.get('query', {}).get('allpages', {}):
            prop = m.get('title', '')[len('Property:'):]

            mainsnak_count = query_mainsnak_uses(prop)
            total[prop] = mainsnak_count
            mainsnak[prop] = mainsnak_count

            qualifier_count = query_qualifier_uses(prop)
            total[prop] += qualifier_count
            qualifiers[prop] = qualifier_count

            reference_count = query_reference_uses(prop)
            total[prop] += reference_count
            references[prop] = reference_count

            print(strftime('%Y-%m-%d, %H:%M:%S'), prop, mainsnak_count, qualifier_count, reference_count, total[prop])

        if 'continue' not in data:
            break

        apcontinue = data.get('continue', {}).get('apcontinue', '')

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
