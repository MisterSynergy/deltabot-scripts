#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from typing import Any, Generator, Optional

import pywikibot as pwb
from pywikibot.exceptions import SpamblacklistError
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT = f'{requests.utils.default_user_agent()} (property_list_by_cat.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'

WD = 'http://www.wikidata.org/entity/'
WIKIBASE = 'http://wikiba.se/ontology#'


def query_wdqs(query) -> Generator[dict[str, Any], None, None]:
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
        raise RuntimeError('Cannot parse response as JSON') from exception

    for row in data.get('results', {}).get('bindings', []):
        yield row


def get_value(data_value:Any, url_formatter:Optional[str]) -> str:
    if isinstance(data_value, pwb.ItemPage) or isinstance(data_value, pwb.PropertyPage):
        return data_value.getID()

    if isinstance(data_value, pwb.WbQuantity):
        if data_value.unit == '1':
            return str(data_value.amount)

        return f'{data_value.amount} {{{{label|{data_value.unit[31:]}}}}}'

    if isinstance(data_value, pwb.FilePage):
        return data_value.title()[5:]

    if isinstance(data_value, pwb.WbTime):
        if data_value.precision == 11:
            return f'{data_value.year:04d}-{data_value.month:02d}-{data_value.day:02d}'

        if data_value.precision == 10:
            return f'{data_value.year:04d}-{data_value.month:02d}'

        return f'{data_value.year:04d}'

    if isinstance(data_value, pwb.Coordinate):
        return f'{data_value.lat:7.4f}/{data_value.lon:7.4f}'

    if isinstance(data_value, pwb.WbMonolingualText):
        return f'{data_value.text} ({data_value.language})'

    if 'id' in data_value:
        return data_value['id']

    if url_formatter is not None:
        data_value = f'[{url_formatter.replace("$1", data_value)} {data_value}]'

    return str(data_value)


def create_section(qid:str, page_title:str, property_path:str) -> Optional[str]:
    text = '{{List of properties/Header}}\n'

    query = f"""SELECT DISTINCT ?prop ?datatype ?pair_num WHERE {{
        ?prop {property_path} wd:{qid}; wikibase:propertyType ?datatype .
        OPTIONAL {{
            ?prop wdt:P1696 ?pair .
            BIND(SUBSTR(STR(?pair), 33) AS ?pair_num) .
        }}
    }} ORDER BY xsd:integer(SUBSTR(STR(?prop), 33))"""
    data = list(query_wdqs(query))

    if len(data) == 0:
        return None

    if len(data) > 1000 and page_title.count('/') <= 1:
        item = pwb.ItemPage(REPO, qid)
        item.get()

        if 'P1269' in item.claims:
            sublabel1 = item.claims['P1269'][0].getTarget().get()['labels']['en']  # TODO
            if sublabel1 in page_title and len(item.claims['P1269']) > 1:
                page_title += f'/{item.claims["P1269"][1].getTarget().get()["labels"]["en"]}'  # TODO
            else:
                page_title += f'/{sublabel1}'
        else:
            page_title += f'/{item.labels["en"]}'  # TODO

        create_category_page(page_title, qid)

        return f"''see [[Wikidata:List of properties/{page_title}]]''\n\n"

    for row in data:
        pid = row.get('prop', {}).get('value', '').replace(WD, '')
        if not pid.startswith('P'):
            continue

        if pid in ['P5267', 'P5540']:
            continue # Wikimedia spam black list

        datatype = row.get('datatype', {}).get('value', '').replace(WIKIBASE, '').lower()
        pair = row.get('pair_num', {}).get('value', '')

        property_page = pwb.PropertyPage(REPO, pid)
        property_page.get()
        try:
            if 'P1855' in property_page.claims:
                subject = property_page.claims['P1855'][0].getTarget().getID()  # TODO
                obj = property_page.claims['P1855'][0].qualifiers[pid][0].getTarget()  # TODO
            else:
                subject, obj = '', ''  # TODO

            if 'P1630' in property_page.claims:
                url_formatter = property_page.claims['P1630'][0].getTarget()  # TODO
            else:
                url_formatter = None

            objectvalue = get_value(obj, url_formatter)
            text += f'{{{{List of properties/Row|id={pid[1:]}|example-subject={subject}|example-object={objectvalue}|pair={pair}|datatype={datatype}|noexpensivecalls=1}}}}\n'
        except:  # TODO
            text += f'{{{{List of properties/Row|id={pid[1:]}|pair={pair}|datatype={datatype}|noexpensivecalls=1}}}}\n'

    text += '{{Template:List_of_properties/Footer}}\n\n'

    return text


def create_category_page(page_title:str, qid:str) -> None:
    print(page_title)

    text = f'{{{{Q|{qid}}}}}\n'

    query = f'SELECT ?item WHERE {{ ?item wdt:P279 wd:{qid}}} ORDER BY xsd:integer(SUBSTR(STR(?item), STRLEN(STR(wd:))+2))'
    data = list(query_wdqs(query))

    if len(data) > 0:  # qid has subclasses
        for row in data:
            qid_section = row.get('item', {}).get('value', '').replace(WD, '')

            section_text = create_section(qid_section, page_title, 'wdt:P31/wdt:P279*')
            if section_text is not None:
                text += f'=== {{{{label|{qid_section}}}}} ===\n{section_text}'

        other_text = create_section(qid, page_title, 'wdt:P31')
        if other_text is not None:
            text += f'=== Other ===\n{other_text}'

    else:
        other_text = create_section(qid, page_title, 'wdt:P31')
        if other_text is not None:
            text += other_text

    text += f'[[Category:Wikidata:List of properties|{page_title}]]'

    page = pwb.Page(SITE, f'Wikidata:List of properties/{page_title}')
    page.text = text
    try:
        page.save(summary='upd', minor=False)
    except SpamblacklistError:
        print(f'Cannot save "Wikidata:List of properties/{page_title}" due to spam blacklist issue')
        # do not do anything else at this point


def create_overview() -> dict[str, str]:
    query = """SELECT ?item (GROUP_CONCAT(?qfacet; SEPARATOR=', ') AS ?facets) (GROUP_CONCAT(?label; SEPARATOR=', ') AS ?labels) WHERE {
        ?item wdt:P279 wd:Q18616576 .
        OPTIONAL {
            ?item wdt:P1269 ?facet .
            ?facet rdfs:label ?facetlabel .
            FILTER (LANG(?facetlabel) = 'en') .
        }
        BIND(IF(BOUND(?facet), SUBSTR(STR(?facet), 32), SUBSTR(STR(?item), 32)) AS ?qfacet) .
        ?item rdfs:label ?itemlabel .
        FILTER(LANG(?itemlabel) = 'en') .
        BIND(IF(BOUND(?facet), STR(?facetlabel), STR(?itemlabel)) AS ?label) .
    } GROUP BY ?item ORDER BY fn:lower-case(?labels)"""

    query_wdqs(query)
    
    cat1st:dict[str, str] = {}
    text = ''
    i = 0
    for row in query_wdqs(query):
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        link = row.get('labels', {}).get('value', '').split(',')[0]

        if ':' in link:
            link = row.get('labels', {}).get('value', '').split(':')[1]

        n = 2
        while link in cat1st:
            link = f'{link} ({n})'
            n += 1

        cat1st[link] = qid

        facets = row.get('facets', {}).get('value')
        if facets is None or len(facets) == 0:
            label = ''
        else:
            label = f'{{{{{"}}, {{label|Q}}".join(facets.split(", "))}}}}}'

        if i % 5 == 0:  # five columns on https://www.wikidata.org/wiki/Wikidata:List_of_properties
            text += '|-\n'
        text += f"""| style="background-color:#eee; box-shadow: 0 0 .2em #999; border-radius: .2em; padding: 20px; width:20%; font-size:105%;" |
'''[[Wikidata:List of properties/{link}|{label}]]'''
"""

        i += 1

    page = pwb.Page(SITE, 'Wikidata:List of properties/cat overview')  # transcluded by https://www.wikidata.org/wiki/Wikidata:List_of_properties
    page.text = text
    page.save(summary='upd', minor=False)     

    return cat1st


def main() -> None:
    cat1st = create_overview()
    for cat in cat1st:
        create_category_page(cat, cat1st[cat])


if __name__=='__main__':
    main()    
