#!/usr/bin/python
#  -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from time import sleep
from typing import Generator

import pywikibot as pwb
from pywikibot.data import api
from pywikibot.exceptions import OtherPageSaveError
import requests


SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()

ERROR_THRESHOLD = 50

PETSCAN_ENDPOINT = 'https://petscan.wmcloud.org/'
PETSCAN_SLEEP = 1
USER_AGENT = f'{requests.utils.default_user_agent()} (badges.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'


def get_badge_job_definitions() -> list[dict[str, str]]:
    response = requests.get(
        url='https://www.wikidata.org/wiki/User:DeltaBot/badges',
        params={
            'action' : 'raw',
        },
        headers={
            'User-Agent' : USER_AGENT,
        }
    )

    try:
        payload = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError('Cannot parse badge definition as JSON') from exception

    return payload


def query_petscan(payload:dict[str, str]) -> Generator[str, None, None]:
    response = requests.post(
        url=PETSCAN_ENDPOINT,
        data=payload,
        headers={ 'User-Agent' : USER_AGENT }
    )
    sleep(PETSCAN_SLEEP)

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError(f'Cannot parse petscan response as JSON; HTTP status {response.status_code}; time elapsed {response.elapsed.total_seconds():.2f} s') from exception

    if len(data.get('*', [])) != 1:
        return

    if len(data.get('*', [])[0].get('a', {}).get('*', [])) > ERROR_THRESHOLD:
        raise RuntimeError(f'Found too many cases: {len(data.get("*", [])[0].get("a", {}).get("*", []))} for {payload.get("language")}, {payload.get("project")}')

    for row in data.get('*', [])[0].get('a', {}).get('*', []):
        qid = row.get('title')
        if qid is None:
            continue

        yield qid


def get_available_badges() -> list[str]:
    request = api.Request(site=SITE, parameters={'action' : 'wbavailablebadges'})
    response = request.submit()
    payload = response.get('badges', [])

    return payload


def remove_badge(item:pwb.ItemPage, dbname:str, badge_qid:str) -> None:
    sitelink = item.sitelinks.get(dbname)
    if sitelink is None:
        return

    new_badges = [ item_page for item_page in sitelink.badges if item_page.title()!=badge_qid ]
    if new_badges == sitelink.badges:
        return

    new_sitelink = pwb.SiteLink(
        sitelink.canonical_title(),
        site=dbname,
        badges=new_badges
    )

    item.setSitelink(
        new_sitelink,
        summary=f'remove badge [[{badge_qid}]] from {dbname} sitelink'
    )


def add_badge(item:pwb.ItemPage, dbname:str, badge_qid:str) -> None:
    sitelink = item.sitelinks.get(dbname)
    if sitelink is None:
        return

    if badge_qid in [ item_page.title() for item_page in sitelink.badges ]:
        return

    new_badges = [
        *sitelink.badges,
        pwb.ItemPage(REPO, badge_qid)
    ]
    new_sitelink = pwb.SiteLink(
        sitelink.canonical_title(),
        site=dbname,
        badges=new_badges
    )

    try:
        item.setSitelink(
            new_sitelink,
            summary=f'add badge [[{badge_qid}]] to {dbname} sitelink'
        )
    except OtherPageSaveError as exception:
        print(exception)


def remove_badges(task:dict[str, str]) -> None:
    category = task.get('category')
    language = task.get('language')
    project = task.get('project')
    badge_qid = task.get('badge')
    dbname = task.get('site')
    if category is None or language is None or project is None or badge_qid is None or dbname is None:
        return

    petscan_payload = {
        'categories' : category,
        'language' : language,
        'project' : project,
        'sparql' : f'SELECT ?item WHERE {{ ?article schema:about ?item; wikibase:badge wd:{badge_qid}; schema:isPartOf <https://{language}.{project}.org/> }}',
        'source_combination' : 'sparql not categories',
        'ns[0]' : '1',
        'ns[100]' : '1',
        'common_wiki' : 'wikidata',
        'format' : 'json',
        'doit' : 'Do it!',
    }

    try:
        for qid in query_petscan(petscan_payload):
            item = pwb.ItemPage(REPO, qid)
            remove_badge(item, dbname, badge_qid)
    except RuntimeError as exception:
        print(exception)


def add_badges(task:dict[str, str], available_badges:list[str]) -> None:
    category = task.get('category')
    language = task.get('language')
    project = task.get('project')
    badge_qid = task.get('badge')
    dbname = task.get('site')
    if category is None or language is None or project is None or badge_qid is None or dbname is None:
        return

    if badge_qid not in available_badges:
        return

    petscan_payload = {
        'categories' : category,
        'language' : language,
        'project' : project,
        'sparql' : f'SELECT ?item WHERE {{ ?article schema:about ?item; wikibase:badge wd:{badge_qid}; schema:isPartOf <https://{language}.{project}.org/> }}',
        'source_combination' : 'categories not sparql',
        'ns[0]' : '1',
        'ns[100]' : '1',
        'common_wiki' : 'wikidata',
        'format' : 'json',
        'doit' : 'Do it!',
    }

    try:
        for qid in query_petscan(petscan_payload):
            item = pwb.ItemPage(REPO, qid)
            add_badge(item, dbname, badge_qid)
    except RuntimeError as exception:
        print(exception)


def main() -> None:
    tasks = get_badge_job_definitions()
    available_badges = get_available_badges()

    for task in tasks:
        remove_badges(task)
        add_badges(task, available_badges)


if __name__=='__main__':
    main()
