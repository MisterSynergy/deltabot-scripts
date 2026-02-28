#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from json.decoder import JSONDecodeError
from pathlib import Path
import re
import sys
from time import strftime
from typing import Any, Generator, Optional

import mariadb
import pywikibot as pwb
import requests


SITE = pwb.Site('wikidata', 'wikidata')

LOGFILE = Path.home() / 'logs/merge-project-log.dat'
DB_DEFAULT_FILE = Path.home() / 'replica.my.cnf'

TOOL_HOST = 'tools.db.svc.wikimedia.cloud'
TOOL_DB = 's53100__merge_status'
WIKIDATA_REPLICA_HOST = 'wikidatawiki.analytics.db.svc.wikimedia.cloud'
WIKIDATA_REPLICA_DB = 'wikidatawiki_p'

WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USERAGENT = f'{requests.utils.default_user_agent()} (User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'

WD_API_ENDPOINT = 'https://www.wikidata.org/w/api.php'

WD_NUM = 'http://www.wikidata.org/entity/Q'
ALL_INCREMENT = 150
WHITELIST_PROPERTIES = [ 'P1889', 'P629', 'P747', 'P144', 'P4969' ]


class Replica:
    def __init__(self, host:str, dbname:str) -> None:
        self.connection = mariadb.connect(
            host=host,
            database=dbname,
            default_file=str(DB_DEFAULT_FILE),
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def __enter__(self):
        return (self.connection, self.cursor)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.connection.close()


def query_wdqs(query:str) -> Generator[dict[str, Any], None, None]:
    response = requests.get(
        url=WDQS_ENDPOINT,
        params={
            'query' : query,
            'format' : 'json',
        },
        headers={
            'Accept' : 'application/sparql-results+json',
            'User-Agent': WDQS_USERAGENT,
        }
    )

    try:
        data = response.json()
    except JSONDecodeError as exception:
        raise RuntimeError('Cannot parse result from SPARQL endpoint') from exception

    for row in data.get('results', {}).get('bindings', []):
        yield row


#database queries
def get_items(dbname_1:str, dbname_2:str, cat_1:Optional[str], cat_2:Optional[str]) -> Generator[dict[str, str|int], None, None]:
    query_1 = f"""SELECT
    a.ips_item_id AS ips_item_id_a,
    b.ips_item_id AS ips_item_id_b,
    CONVERT(a.ips_site_page USING utf8) AS ips_site_page_a,
    CONVERT(b.ips_site_page USING utf8) AS ips_site_page_b
FROM (
    SELECT
        ips_item_id,
        ips_site_page
    FROM
        wb_items_per_site
    WHERE
        ips_item_id NOT IN (
            SELECT
                ips_item_id
            FROM
                wb_items_per_site
            WHERE
                ips_site_id=%(dbname1)s
        )
        AND ips_site_id=%(dbname2)s
)a INNER JOIN (
    SELECT
        ips_item_id,
        ips_site_page
    FROM
        wb_items_per_site
    WHERE
        ips_item_id NOT IN (
            SELECT
                ips_item_id
            FROM
                wb_items_per_site
            WHERE
                ips_site_id=%(dbname2)s
        )
        AND ips_site_id=%(dbname1)s
)b ON a.ips_site_page=b.ips_site_page"""

    params = { 'dbname1' : dbname_1, 'dbname2' : dbname_2 }

    with Replica(WIKIDATA_REPLICA_HOST, WIKIDATA_REPLICA_DB) as (_, cur):
        cur.execute(query_1, params)

        for row in cur.fetchall():
            yield row

        if cat_1 is not None:
            query = f"""SELECT
              a.ips_item_id AS ips_item_id_a,
              b.ips_item_id AS ips_item_id_b,
              CONVERT(a.ips_site_page USING utf8) AS ips_site_page_a,
              CONVERT(b.ips_site_page USING utf8) AS ips_site_page_b
            FROM (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                    ips_item_id
                  FROM
                    wb_items_per_site
                  WHERE
                    ips_site_id=%(dbname1)s
                )
                AND ips_site_id=%(dbname2)s
            )a INNER JOIN (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                    ips_item_id
                  FROM
                    wb_items_per_site
                  WHERE
                    ips_site_id=%(dbname2)s
                )
                AND ips_site_id=%(dbname1)s
            )b ON CONCAT(%(cat1)s,":",a.ips_site_page)=b.ips_site_page"""
            params = { 'dbname1' : dbname_1, 'dbname2' : dbname_2, 'cat1' : cat_1 }

            cur.execute(query, params)
            for row in cur.fetchall():
                yield row

        if cat_2 is not None:
            query = f"""SELECT
              a.ips_item_id AS ips_item_id_a,
              b.ips_item_id AS ips_item_id_b,
              CONVERT(a.ips_site_page USING utf8) AS ips_site_page_a,
              CONVERT(b.ips_site_page USING utf8) AS ips_site_page_b
            FROM (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                    ips_item_id
                  FROM
                    wb_items_per_site
                  WHERE
                    ips_site_id=%(dbname1)s
                )
                AND ips_site_id=%(dbname2)s
            )a INNER JOIN (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                  ips_item_id
                  FROM
                  wb_items_per_site
                  WHERE
                  ips_site_id=%(dbname2)s
                )
                AND ips_site_id=%(dbname1)s
            )b ON a.ips_site_page = CONCAT(%(cat2)s,":",b.ips_site_page)"""
            params = { 'dbname1' : dbname_1, 'dbname2' : dbname_2, 'cat2' : cat_2 }

            cur.execute(query, params)
            for row in cur.fetchall():
                yield row

        if cat_1 is not None and cat_2 is not None:
            query = f"""SELECT
              a.ips_item_id AS ips_item_id_a,
              b.ips_item_id AS ips_item_id_b,
              CONVERT(a.ips_site_page USING utf8) AS ips_site_page_a,
              CONVERT(b.ips_site_page USING utf8) AS ips_site_page_b
            FROM (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                    ips_item_id
                  FROM
                    wb_items_per_site
                  WHERE
                    ips_site_id=%(dbname1)s
                )
                AND ips_site_id=%(dbname2)s
            )a INNER JOIN (
              SELECT
                ips_item_id,
                ips_site_page
              FROM
                wb_items_per_site
              WHERE
                ips_item_id NOT IN (
                  SELECT
                    ips_item_id
                  FROM
                    wb_items_per_site
                  WHERE
                    ips_site_id=%(dbname2)s
                )
                AND ips_site_id=%(dbname1)s
            )b ON CONCAT(%(cat1)s,":",a.ips_site_page) = CONCAT(%(cat2)s,":",b.ips_site_page)"""
            params = { 'dbname1' : dbname_1, 'dbname2' : dbname_2, 'cat1' : cat_1, 'cat2' : cat_2 }

            cur.execute(query, params)
            for row in cur.fetchall():
                yield row


def update_list(whitelist:list[list[int]], names:list[int], disam:list[int], id:int, dbname_1:str, dbname_2:str, interwiki_prefix_1:str, interwiki_prefix_2:str, cat_1:Optional[str], cat_2:Optional[str]) -> None:
    # because this script can run in parallel, check again if the selected list is not already updating
    with Replica(TOOL_HOST, TOOL_DB) as (conn, cur):
        cur.execute(f'SELECT update_running FROM merge_status WHERE id=%(identifier)s', { 'identifier' : id })

        for row in cur.fetchall():
            if row.get('update_running') is None:
                continue

            print(row.get('update_running'), 'update is currently running')
            return

        # if it is not updating, set status to updating
        cur.execute(f'UPDATE merge_status SET update_running=NOW() WHERE id=%(identifier)s', { 'identifier' : id })
        conn.commit()

    pretext = ''
    accepted = 0
    excluded = 0

    for row in get_items(dbname_1, dbname_2, cat_1, cat_2):
        qid_num_1 = row.get('ips_item_id_a')
        qid_num_2 = row.get('ips_item_id_b')
        page_title_1 = row.get('ips_site_page_a')
        page_title_2 = row.get('ips_site_page_b')

        if qid_num_1 is None or qid_num_2 is None or page_title_1 is None or page_title_2 is None:
            continue

        if (qid_num_1 not in disam and qid_num_2 in disam) or (qid_num_1 in disam and qid_num_2 not in disam):
            continue

        if (qid_num_1 in names) or (qid_num_2 in names):
            continue

        if [qid_num_1, qid_num_2] in whitelist or [qid_num_2, qid_num_1] in whitelist:
            excluded+=1
        else:
            accepted+=1
            pretext += f'# [[Q{qid_num_1}]] ([[:{interwiki_prefix_1}:{page_title_1}]]) and [[Q{qid_num_2}]] ([[:{interwiki_prefix_2}:{page_title_2}]])\n'

    #write text
    text = f"""{{{{User:Pasleim/projectmerge/header
|wiki1={dbname_1}
|wiki2={dbname_2}
|candidates={excluded+accepted}
|excluded={excluded}
|remaining={accepted}
|update={strftime('%Y-%m-%d %H:%M (%Z)')}
}}}}"""

    if accepted > 0:
        text += f'\n\n== Merge candidates ==\n{pretext}'

    # write to Wikidata
    page = pwb.Page(SITE, f'User:Pasleim/projectmerge/{dbname_1}-{dbname_2}')

    if accepted > 0 or page.exists():
        page.text = text
        page.save(summary='upd', minor=False)

    with Replica(TOOL_HOST, TOOL_DB) as (conn, cur):
        cur.execute(
            f'UPDATE merge_status SET last_update=%(timestmp)s, candidates=%(accepted)s, update_running="0000-00-00 00:00:00" WHERE id=%(identifier)s',
            { 'timestmp' : strftime("%Y-%m-%d %H:%M:%S"), 'accepted' : accepted, 'identifier' : id }
        )
        conn.commit()

    with open(LOGFILE, mode='a') as file_handle:
        file_handle.write(f'{strftime("%Y-%m-%d %H:%M (%Z)")}\tupdate {dbname_1} {dbname_2}\n')


def load_disam() -> list[int]:
    disam:list[int] = []

    for row in query_wdqs('SELECT ?item WHERE{ ?item wdt:P31/wdt:P279* wd:Q4167410 }'):
        qid = row.get('item', {}).get('value')
        if qid is None:
            continue

        if WD_NUM not in qid:
            continue

        disam.append(int(qid.replace(WD_NUM, '')))

    return disam


def load_names() -> list[int]:
    names:list[int] = []

    for row in query_wdqs('SELECT ?item WHERE { ?item wdt:P31/wdt:P279* wd:Q82799 }'):
        try:
            qid_num = int(row.get('item', {}).get('value', '').replace(WD_NUM, ''))
        except ValueError:  # avoid issues with somevalue results and so on
            continue

        names.append(qid_num)

    return names


def load_whitelist_from_sparql() -> list[list[int]]:
    whitelist:list[list[int]] = []

    for prop in WHITELIST_PROPERTIES:
        for row in query_wdqs(f'SELECT ?item ?item2 WHERE {{ ?item wdt:{prop} ?item2 . MINUS {{ ?item rdf:type wikibase:Property }} MINUS {{ ?item rdf:type ontolex:LexicalEntry }} }}'):
            try:
                qid_num_1 = int(row.get('item', {}).get('value', '').replace(WD_NUM, ''))
                qid_num_2 = int(row.get('item2', {}).get('value', '').replace(WD_NUM, ''))
            except ValueError:  # avoid issues with somevalue results and so on
                continue

            whitelist.append(
                [
                    qid_num_1,
                    qid_num_2,
                ]
            )

    return whitelist


def load_whitelist_from_do_not_merge() -> list[list[int]]:
    whitelist:list[list[int]] = []

    response = requests.get(
        url=WD_API_ENDPOINT,
        params={
            'action' : 'query',
            'list' : 'allpages',
            'apprefix' : 'Do not merge/',
            'apnamespace' : '4',
            'aplimit' : '500',
            'format' : 'json',
        }
    )

    data = response.json()

    for page_dct in data.get('query', {}).get('allpages', []):
        page = pwb.Page(SITE, page_dct.get('title', ''))

        if page.isRedirectPage():
            continue

        text = page.get()

        for match in re.findall(r'Q(\d+)(.*)Q(\d+)', text):
            whitelist.append(
                [
                    int(match[0]),
                    int(match[2]),
                ]
            )

    return whitelist


def query_backlog(argv:str) -> list[dict[str, Any]]:
    # select which lists need an update
    if argv == 'all':
        query = f"""SELECT
            id,
            wiki1,
            wiki2,
            CONVERT(cat1 USING utf8) AS cat1,
            CONVERT(cat2 USING utf8) AS cat2
        FROM
            merge_status
        WHERE
            TIMESTAMPDIFF(DAY, last_update, NOW())>6
            AND update_running='0000-00-00 00:00:00'
        ORDER BY
            TIMESTAMPDIFF(DAY, last_update, NOW()) DESC
        LIMIT
            {ALL_INCREMENT}"""
    elif argv == 'upd':
        query = """SELECT
            id,
            wiki1,
            wiki2,
            CONVERT(cat1 USING utf8) AS cat1,
            CONVERT(cat2 USING utf8) AS cat2
        FROM
            merge_status
        WHERE
            update_requested>last_update
            AND update_running='0000-00-00 00:00:00'"""
    else:
        raise RuntimeError(f'Invalid argv "{argv}" provided (only "all" and "upd" are allowed)')

    with Replica(TOOL_HOST, TOOL_DB) as (conn, cur):
        cur.execute('UPDATE merge_status SET update_running="0000-00-00 00:00:00" WHERE TIMESTAMPDIFF(DAY, update_running, NOW())>1')
        conn.commit()

        cur.execute(query)
        result = cur.fetchall()

    return result


def make_interwiki_prefix(dbname:str) -> str:
    suffixes = {
        'wiki' : '',
        'wikiquote' : 'q:',
        'wikisource' : 's:',
        'wikivoyage' : 'voy:',
        'wikinews' : 'n:',
        'wikibooks' : 'b:',
        'wikiversity' : 'v:',
        'wiktionary' : 'wikt:',
        'species' : 'species:',
    }

    for suffix, short in suffixes.items():
        if dbname.endswith(suffix):
            return f'{short}{dbname[:-1*len(suffix)]}'.replace('_', '-')

    raise RuntimeError(f'Cannot determine interwiki prefix for {dbname}')


def main():
    try:
        argv = sys.argv[1]
    except:
        return

    backlog = query_backlog(argv)
    if len(backlog) == 0:
        return

    #create whitelist from Do_not_merge and links based on sparql
    whitelist = [
        *load_whitelist_from_do_not_merge(),
        *load_whitelist_from_sparql(),
    ]

    #load all names
    names = load_names()

    #load all disam-items
    disam = load_disam()

    for row in backlog:
        merge_status_id = row.get('id')
        dbname_1 = row.get('wiki1')
        dbname_2 = row.get('wiki2')
        cat_1 = row.get('cat1')
        cat_2 = row.get('cat2')

        try:
            interwiki_prefix_1 = make_interwiki_prefix(dbname_1)
            interwiki_prefix_2 = make_interwiki_prefix(dbname_2)
        except RuntimeError as exception:
            print(dbname_1, dbname_2, exception)
            continue

        update_list(whitelist, names, disam, merge_status_id, dbname_1, dbname_2, interwiki_prefix_1, interwiki_prefix_2, cat_1, cat_2)

        #print('error update_list')
        #with open(LOGFILE, mode='a') as file_handle:
        #    file_handle.write(f'{strftime("%Y-%m-%d %H:%M (%Z)")}\terror {dbname_1} {dbname_2}\n')


if __name__ == '__main__':
    main()
