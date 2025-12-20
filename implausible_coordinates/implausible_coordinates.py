#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import json
from json.decoder import JSONDecodeError
import operator
from pathlib import Path
from typing import Generator

import requests
import pywikibot as pwb


def read_input() -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int], dict[str, str]]:
    with open(Path.home() / 'jobs/implausible_coordinates/implausible_coordinates_borders.json', mode='r', encoding='utf8') as file_handle:
       data = json.load(file_handle)

    north:dict[str, int] = data.get('north', {})
    south:dict[str, int] = data.get('south', {})
    west:dict[str, int] = data.get('west', {})
    east:dict[str, int] = data.get('east', {})
    countries:dict[str, str] = data.get('countries', {})

    return north, south, west, east, countries


def query_wdqs(query:str) -> Generator[dict[str, dict], None, None]:
    response = requests.post(
        url='https://query.wikidata.org/bigdata/namespace/wdq/sparql',
        data={
            'query': query,
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': f'{requests.utils.default_user_agent()} (implausible_coordinates.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)',
        },
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        raise RuntimeWarning(f'Cannot parse WDQS response as JSON; query: {query}') from exception

    for row in payload.get('results', {}).get('bindings', []):
        yield row


def main() -> None:
    north, south, west, east, countries = read_input()

    text = '== Implausible Coordinate ==\n'

    sorted_countries = sorted(countries.items(), key=operator.itemgetter(1))
    for qid_numeric, country_name in sorted_countries:
        west_boundary = west.get(country_name)
        east_boundary = east.get(country_name)
        south_boundary = south.get(country_name)
        north_boundary = north.get(country_name)

        if west_boundary is None or east_boundary is None or south_boundary is None or north_boundary is None:
            continue

        query = f"""SELECT DISTINCT ?item WHERE {{
  ?item wdt:P17 wd:Q{qid_numeric}; p:P625/psv:P625 ?node .
  ?node wikibase:geoLatitude ?lat; wikibase:geoLongitude ?lon .
  FILTER (?lon < {west_boundary} || ?lon > {east_boundary} || ?lat < {south_boundary} || ?lat > {north_boundary}) .
  OPTIONAL {{
    ?item wdt:P17 ?country2 .
    FILTER (?country2 != wd:Q{qid_numeric}) .
  }}
  FILTER (!BOUND(?country2)) .
}}"""

        headline_written = False
        for row in query_wdqs(query):
            qid = row.get('item', {}).get('value', '').replace('http://www.wikidata.org/entity/', '')

            if headline_written is False:
                headline_written = True
                text += f'\n=== {country_name} ===\n'

            text += f'[[{qid}]], '

    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'User:Pasleim/Implausible/coordinate')
    page.text = text
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
