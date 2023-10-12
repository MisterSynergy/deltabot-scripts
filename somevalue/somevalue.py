#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from typing import Any, Generator, Optional

import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

WD_API_ENDPOINT = 'https://wikidata.org/w/api.php'
WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USER_AGENT = f'{requests.utils.default_user_agent()} (somevalue.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'
WDS = 'http://www.wikidata.org/entity/statement/'

QUERY = """SELECT DISTINCT ?snak_type_item ?entity ?statement ?main_property ?location ?location_property WHERE {
  VALUES ?snak_type_item { wd:Q53569537 wd:Q108474139 }
  {
    ?statement ?ps ?snak_type_item .
    ?entity ?p ?statement .
    ?main_property wikibase:claim ?p; wikibase:statementProperty ?ps .
    BIND('mainsnak' AS ?location) .
  } UNION {
    ?statement ?pq ?snak_type_item .
    ?entity ?p ?statement .
    ?location_property wikibase:qualifier ?pq .
    ?main_property wikibase:claim ?p .
    BIND('qualifier' AS ?location) .
  } UNION {
    ?statement prov:wasDerivedFrom [ ?pr ?snak_type_item ] .
    ?entity ?p ?statement .
    ?location_property wikibase:reference ?pr .
    ?main_property wikibase:claim ?p .
    BIND('reference' AS ?location) .
  }
  FILTER(?entity NOT IN (wd:Q53569537, wd:Q108474139)) .
}"""

MAPPING = {
    'Q53569537' : 'somevalue',
    'Q108474139' : 'novalue',
}


def query_wdqs(query:str) -> Generator[dict[str, Any], None, None]:
    response = requests.post(
        url=WDQS_ENDPOINT,
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


def get_claims_via_wbgetentities(qid:str) -> dict[str, list[dict[str, Any]]]:
    response = requests.get(
        url=WD_API_ENDPOINT,
        params={
            'action' : 'wbgetentities',
            'ids' : qid,
            'format' : 'json',
        }
    )

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse MWAPI response as JSON; HTTP status {response.status_code}; query time {response.elapsed.total_seconds:.2f} sec') from exception

    return data.get('entities', {}).get(qid, {}).get('claims', {})


def is_movable_claim(snak:Optional[dict[str, Any]], snak_type_qid:str) -> bool:
    if snak is None:
        return False

    if snak.get('datatype') != 'wikibase-item':
        return False

    if snak.get('datavalue', {}).get('value', {}).get('id') != snak_type_qid:
        return False

    return True


def move(qid:str, claim:dict[str, Any], snak_type:str, snak_type_qid:str) -> None:
    payload = {
        'claims' : [ claim ],
    }

    item = pwb.ItemPage(REPO, qid)
    item.editEntity(payload, summary=f'update claim: [[{snak_type_qid}]] -> <{snak_type}>')


def transform_statement_id(statement_id:Optional[str]) -> str:
    if statement_id is None:
        raise RuntimeError(f'Cannot transform statement_id=None')

    return statement_id.replace('$', '-').upper()


def process_mainsnak(snak_type_qid:str, entity_qid:str, statement_id:str, main_property_pid:str) -> None:
    snak_type = MAPPING.get(snak_type_qid)
    if snak_type is None:
        return

    if entity_qid[0] in [ 'E', 'L' ]:  # skip EntitySchema and Lexeme namespaces
        return

    try:
        claim_dct = get_claims_via_wbgetentities(entity_qid)
    except RuntimeError as exception:
        print(snak_type_qid, entity_qid, statement_id, main_property_pid, exception)
        return

    for claim in claim_dct.get(main_property_pid, []):
        if transform_statement_id(claim.get('id')) != statement_id:
            continue

        if is_movable_claim(claim.get('mainsnak'), snak_type_qid):
            claim['mainsnak'].pop('datavalue')
            claim['mainsnak']['snaktype'] = snak_type
            move(entity_qid, claim, snak_type, snak_type_qid)


def process_qualifier(snak_type_qid:str, entity_qid:str, statement_id:str, main_property_pid:str, location_property_pid:str) -> None:
    snak_type = MAPPING.get(snak_type_qid)
    if snak_type is None:
        return

    if entity_qid[0] in [ 'E', 'L' ]:  # skip EntitySchema and Lexeme namespaces
        return

    try:
        claim_dct = get_claims_via_wbgetentities(entity_qid)
    except RuntimeError as exception:
        print(snak_type_qid, entity_qid, statement_id, main_property_pid, location_property_pid, exception)
        return

    for claim in claim_dct.get(main_property_pid, []):
        if transform_statement_id(claim.get('id')) != statement_id:
            continue

        if 'qualifiers' not in claim:
            continue

        for i, qualifier_snak in enumerate(claim.get('qualifiers', {}).get(location_property_pid, [])):
            if is_movable_claim(qualifier_snak, snak_type_qid):
                claim['qualifiers'][location_property_pid][i].pop('datavalue')
                claim['qualifiers'][location_property_pid][i]['snaktype'] = snak_type
                move(entity_qid, claim, snak_type, snak_type_qid)


def process_reference(snak_type_qid:str, entity_qid:str, statement_id:str, main_property_pid:str, location_property_pid:str) -> None:
    snak_type = MAPPING.get(snak_type_qid)
    if snak_type is None:
        return

    if entity_qid[0] in [ 'E', 'L' ]:  # skip EntitySchema and Lexeme namespaces
        return

    try:
        claim_dct = get_claims_via_wbgetentities(entity_qid)
    except RuntimeError as exception:
        print(snak_type_qid, entity_qid, statement_id, main_property_pid, location_property_pid, exception)
        return

    for claim in claim_dct.get(main_property_pid, []):
        if transform_statement_id(claim.get('id')) != statement_id:
            continue

        if 'references' not in claim:
            continue

        for i, reference in enumerate(claim.get('references', [])):
            for j, reference_snak in enumerate(reference.get('snaks', {}).get(location_property_pid, [])):
                if is_movable_claim(reference_snak, snak_type_qid):
                    claim['references'][i]['snaks'][location_property_pid][j].pop('datavalue')
                    claim['references'][i]['snaks'][location_property_pid][j]['snaktype'] = snak_type
                    move(entity_qid, claim, snak_type, snak_type_qid)


def main() -> None:
    try:
        gen = query_wdqs(QUERY)
    except RuntimeError as exception:
        print(exception)
        return

    for row in gen:
        snak_type_qid = row.get('snak_type_item', {}).get('value', '').replace(WD, '')
        if len(snak_type_qid)==0:
            continue

        entity_qid = row.get('entity', {}).get('value', '').replace(WD, '')
        if len(entity_qid)==0:
            continue

        location = row.get('location', {}).get('value')
        if location is None:
            continue

        statement = row.get('statement', {}).get('value', '').replace(WDS, '').upper()
        if location in [ 'mainsnak', 'qualifier', 'reference' ] and len(statement)==0:
            continue

        main_property_pid = row.get('main_property', {}).get('value', '').replace(WD, '')
        if location in [ 'mainsnak', 'qualifier', 'reference' ] and len(main_property_pid)==0:
            continue

        location_property_pid = row.get('location_property', {}).get('value', '').replace(WD, '')
        if location in [ 'qualifier', 'reference' ] and len(location_property_pid)==0:
            continue

        if location == 'mainsnak':
            process_mainsnak(snak_type_qid, entity_qid, statement, main_property_pid)
        elif location == 'qualifier':
            process_qualifier(snak_type_qid, entity_qid, statement, main_property_pid, location_property_pid)
        elif location == 'reference':
            process_reference(snak_type_qid, entity_qid, statement, main_property_pid, location_property_pid)


if __name__=='__main__':
    main()
