#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from collections import Counter
import logging
from os.path import expanduser
from typing import Any, Optional

import mariadb
import requests

import pywikibot as pwb


logging.basicConfig(level=logging.INFO)

SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

PETSCAN_ENDPOINT = 'https://petscan.wmflabs.org/'

# an alternative strategy to manually defined tasks would be to use sitelinks of Q1982926
TASKS = [
    {
        'language': 'cs',
        'site': 'cswiki',
        'project': 'wikipedia',
        'category': 'Wikipedie:Rozcestníky',
        'description': 'rozcestník na projektech Wikimedia',
    },
    {
        'language': 'da',
        'site': 'dawiki',
        'project': 'wikipedia',
        'category': 'Flertydig',
        'description': 'Wikimedia-flertydigside',
    },
    {
        'language': 'de',
        'site': 'dewiki',
        'project': 'wikipedia',
        'category': 'Begriffsklärung',
        'description': 'Wikimedia-Begriffsklärungsseite',
    },
    {
        'language': 'en',
        'site': 'enwiki',
        'project': 'wikipedia',
        'category': 'Disambiguation pages',
        'description': 'Wikimedia disambiguation page',
    },
    {
        'language': 'es',
        'site': 'eswiki',
        'project': 'wikipedia',
        'category': 'Wikipedia:Desambiguación',
        'description': 'página de desambiguación de Wikimedia',
    },
    {
        'language': 'fr',
        'site': 'frwiki',
        'project': 'wikipedia',
        'category': 'Homonymie',
        'description': 'page d\'homonymie de Wikimedia',
    },
    {
        'language': 'it',
        'site': 'itwiki',
        'project': 'wikipedia',
        'category': 'Pagine di disambiguazione',
        'description': 'pagina di disambiguazione di un progetto Wikimedia',
    },
    {
        'language': 'nl',
        'site': 'nlwiki',
        'project': 'wikipedia',
        'category': 'Wikipedia:Doorverwijspagina',
        'description': 'Wikimedia-doorverwijspagina',
    },
    {
        'language': 'pl',
        'site': 'plwiki',
        'project': 'wikipedia',
        'category': 'Strony ujednoznaczniające',
        'description': 'strona ujednoznaczniająca w projekcie Wikimedia',
    },
    {
        'language': 'pt',
        'site': 'ptwiki',
        'project': 'wikipedia',
        'category': 'Desambiguação',
        'description': 'página de desambiguação de um projeto da Wikimedia',
    },
    {
        'language': 'sv',
        'site': 'svwiki',
        'project': 'wikipedia',
        'category': 'Förgreningssidor',
        'neg_category': 'Namnförgreningssidor',
        'description': 'Wikimedia-förgreningssida',
    },
    {  # per request at Topic:Xbbp72w8kcka1pv2
        'language': 'sv',
        'site': 'svwiki',
        'project': 'wikipedia',
        'category': 'Namnförgreningssidor',
        'description': 'särskiljningssida för identiska personnamn',
        'type': 'Q22808320',
    }
]

BRACKET_TERMS:list[str]
BRACKET_TERMS_FILE = f'{expanduser("~")}/jobs/new_disambiguation_pages/new_disambiguation_pages_terms.txt'

DAB_ITEMS = [
    'Q4167410',
    'Q15407973',
    'Q22808320',
    'Q61996773',
    'Q66480449'
]

QUERY_TEMPLATE = """SELECT DISTINCT
  wbit_item_id
FROM
  wbt_item_terms
    JOIN wbt_term_in_lang ON wbit_term_in_lang_id=wbtl_id
      JOIN wbt_text_in_lang ON wbxl_id=wbtl_text_in_lang_id
        JOIN wbt_text ON wbx_id=wbxl_text_id
WHERE
  wbtl_type_id=1
  AND wbx_text=%(literal)s"""


def bracket_terms() -> list[str]:
    with open(BRACKET_TERMS_FILE, mode='r', encoding='utf8') as file_handle:
        bracket_terms = file_handle.readlines()

    return bracket_terms


def remove_brackets(literal:str) -> str:
    """remove brackets with the word "disambiguation page" inside"""
    for term in BRACKET_TERMS:
        literal = literal.replace(f'({term})', '').strip()

    return literal


def is_disambiguation_page(site:str, title:str) -> bool:
    client_site = pwb.APISite.fromDBName(site)

    client_page = pwb.Page(client_site, title)
    client_page.get()

    return client_page.isDisambig()


def is_disambiguation_item(item:pwb.ItemPage) -> bool:
    for claim in item.claims.get('P31', []):
        if claim.getTarget().getID() in DAB_ITEMS:
            return True

    return False


def get_database_cursor():
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf'
    )
    cur = db.cursor(dictionary=True)

    return cur


def query_unconnected_pages_via_petscan(lang:str, project:str, category:str, neg_category:Optional[str]=None) -> list[dict[str, Any]]:
    params = {
        'language': lang,
        'project': project,
        'categories': category,
        'ns[0]': '1',
        'depth': '1',  # TODO: why not more?
        'show_redirects': 'no',
        'wikidata_item': 'without',
        'doit': '1',
        'format': 'json'
    }

    if neg_category is not None:
        params['negcats'] = neg_category

    response = requests.get(
        PETSCAN_ENDPOINT,
        params=params
    )

    payload = response.json()
    if '*' not in payload:
        raise RuntimeError('Received invalid response from Petscan')
    if len(payload['*']) == 0:
        return []

    data = payload['*'][0].get('a', {}).get('*', [])
    logging.info(f'found {len(data)} pages to process for {lang}.{project} (category "{category}")')

    return data


def validate_task(task:dict[str, str]) -> bool:
    required_keys = [
        'category',
        'description',
        'language',
        'project',
        'site',
    ]

    for key in required_keys:
        if key not in task:
            return False

    return True


def get_entity_data(site:str, title:str, title_unformatted:str, language:str, description:str, type_qid:str) -> dict[str, dict[str, Any]]:
    entity_data:dict[str, dict[str, Any]] = {
        'sitelinks': {
            site: {
                'site': site,
                'title': title_unformatted
            }
        },
        'labels': {
            language: {
                'language': language,
                'value': title
            }
        },
        'descriptions': {
            language: {
                'language': language,
                'value': description
            }
        },
        'claims': {
            'P31': [
                {
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P31',
                        'datavalue': {
                            'value': {
                                'entity-type': 'item',
                                'id': type_qid
                            },
                            'type': 'wikibase-entityid'
                        },
                        'datatype': 'wikibase-item'
                    },
                    'type': 'statement',
                    'rank': 'normal'
                }
            ]
        }
    }

    return entity_data


def count_number_of_sitelinks_with_identical_title(cur, title:str) -> dict[str, int]:
    cnt_sitelinks_with_same_title:dict[str, int] = {}  # keys are QIDs, values are number of sitelinks with same title

    cur.execute(QUERY_TEMPLATE, { 'literal' : title })  # queries all items that have $title as label (in any language)
    logging.info(f'found {cur.rowcount} potential items with suitable labels')
    for row in cur.fetchmany(size=50):  # limit to a reasonable number of items in order to avoid extremely long script times
        qid_numeric = row.get('wbit_item_id')
        if qid_numeric is None:
            continue

        qid = f'Q{qid_numeric}'

        item = pwb.ItemPage(REPO, qid)
        if not item.exists():
            continue

        if item.isRedirectPage():
            continue

        item.get()

        if not is_disambiguation_item(item):
            continue

        cnt_sitelinks_with_same_title[qid] = 0
        for sitelink in item.iterlinks():
            if title != remove_brackets(sitelink.title()):
                continue
            cnt_sitelinks_with_same_title[qid] += 1

    cur.fetchall()  # deplete cursor

    logging.info(f'found {len(cnt_sitelinks_with_same_title)} dab items with suitable labels and sitelinks')

    return cnt_sitelinks_with_same_title


def create_new_item(site:str, title:str, title_unformatted:str, language:str, description:str, type_qid:str) -> None:
    entity_data = get_entity_data(site, title, title_unformatted, language, description, type_qid)

    new_item = pwb.ItemPage(REPO)
    new_item.editEntity(data=entity_data)

    logging.info(f'Created new item with sitelink "{title}" for project {site} (language={language}, description="{description}", type_qid={type_qid})')


def add_sitelink_to_existing_item(qid:str, site:str, title:str) -> bool:
    item = pwb.ItemPage(REPO, qid)
    item.get()

    if site in item.sitelinks:
        logging.info(f'Tried to add "{title}" for project {site} to most suitable item page {qid}, but sitelink is already occupied by "{item.sitelinks[site].title}"')
        return False

    item.setSitelink(
        {
            'site': site,
            'title': title,
        }
    )

    logging.info(f'Added sitelink "{title}" for project {site} to item page {qid}')

    return True


def check_for_existing_item(cur, title:str) -> list[tuple[str, int]]:
    cnt_sitelinks_with_same_title = count_number_of_sitelinks_with_identical_title(cur, title)

    item_candidates = Counter(cnt_sitelinks_with_same_title).most_common()

    return item_candidates


def process_page(cur, task:dict[str, str], petscan_query_row:dict[str, Any]) -> None:
    if not is_disambiguation_page(task['site'], petscan_query_row.get('title', '')):
        logging.warn(f'page "{petscan_query_row.get("title", "")}" on {task["site"]} is not a disambiguation page')
        return

    title = remove_brackets(petscan_query_row.get('title', '').replace('_', ' '))

    item_candidates = check_for_existing_item(cur, title)

    for item_candidate in item_candidates:
        success = add_sitelink_to_existing_item(
            item_candidate[0],
            task['site'],
            petscan_query_row['title'],
        )

        if success is True:
            return

    create_new_item(
        task['site'],
        title,
        petscan_query_row['title'],
        task['language'],
        task['description'],
        task.get('type', 'Q4167410'),
    )


def main() -> None:
    cur = get_database_cursor()

    for task in TASKS:
        if validate_task(task) is False:
            logging.warn(f'invalid task definition: {str(task)}')
            continue

        logging.info(f'process for project {task["language"]}.{task["project"]} category {task["category"]}')

        data = query_unconnected_pages_via_petscan(
            task['language'],
            task['project'],
            task['category'],
            task.get('neg_category')
        )

        for petscan_query_row in data:
            logging.info(f'process page "{petscan_query_row.get("title", "")}"')
            process_page(cur, task, petscan_query_row)


if __name__=='__main__':
    BRACKET_TERMS = bracket_terms()
    main()
