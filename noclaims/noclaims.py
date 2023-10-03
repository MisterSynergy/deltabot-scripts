#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from dataclasses import dataclass, field
from json.decoder import JSONDecodeError
from os.path import expanduser
import time
from typing import Generator

import mariadb
import pywikibot as pwb
import requests


# pywikibot config
SITE = pwb.Site('wikidata', 'wikidata')
REPO = SITE.data_repository()
EDIT_SUMMARY = 'Bot: Updating database report'

# wdqs config
WDQS_ENDPOINT = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
WDQS_USERAGENT = f'{requests.utils.default_user_agent()} (noclaims.py via User:DeltaBot at Wikidata; mailto:tools.deltabot@toolforge.org)'
WD = 'http://www.wikidata.org/entity/'

# Wikidata replica config
DB_DEFAULT_FILE = f'{expanduser("~")}/replica.my.cnf'
WIKIDATA_REPLICA_HOST = 'wikidatawiki.analytics.db.svc.wikimedia.cloud'
WIKIDATA_REPLICA_DB = 'wikidatawiki_p'

# templates for output
HEADER = 'A list of items with a sitelink to {lang_code} but without any statements. Data as of <onlyinclude>{timestamp}</onlyinclude>.\n\n'
TABLE_ROW = '* [[{qid}]] - [[{interwiki_prefix}{page_title}]]\n'
TABLE_ROW_OVERVIEW = '{{{{TR otherreport|{dbname}|{lang}|{family}|{url}|{iw}|{ps_lang}|{ps_family}|{cnt_without}|{idx}|{cnt}}}}}\n'
HEADER_OVERVIEW = '{{{{Wikidata:Database reports/without claims by site/header|{timestamp}}}}}\n'
FOOTER_OVERVIEW = '{{Wikidata:Database reports/without claims by site/footer}} __NOINDEX__'

# queries
QUERY_1 = """SELECT
    CONVERT(ips_site_id USING utf8) AS dbname,
    COUNT(*) AS cnt
FROM
    wb_items_per_site
GROUP BY
    ips_site_id
ORDER BY
    cnt DESC"""

QUERY_2 = """SELECT
    COUNT(*) AS cnt
FROM
    page_props,
    wb_items_per_site,
    page
WHERE
    pp_sortkey=0
    AND pp_propname='wb-claims'
    AND pp_page=page_id
    AND CONCAT("Q", ips_item_id)=page_title
    AND page_namespace=0
    AND ips_site_id=%(dbname)s"""

SPARQL_QUERY = """SELECT ?item ?lemma WHERE {{
  ?sitelink schema:about ?item;
            schema:isPartOf <{url}/>;
            schema:name ?lemma .
  ?item wikibase:statements "0"^^xsd:integer .
}} ORDER BY DESC(xsd:integer(SUBSTR(STR(?item), STRLEN("http://www.wikidata.org/entity/Q")+1))) LIMIT 1000"""


INTERWIKI_MAP = {
    'wikipedia' : '',
    'wikibooks' : 'b:',
    'wikiquote' : 'q:',
    'wiktionary' : 'wikt:',
    'wikinews' : 'n:',
    'wikisource' : 's:',
    'wikiversity' : 'v:',
    'wikivoyage' : 'voy:',
    'wikidata' : 'd:',
    'commons' : 'c:',
    'meta' : 'm:',
    'species' : 'species:',
}


@dataclass
class Project:
    dbname:str

    # from meta_p.wiki
    lang:str = field(init=False)
    family:str = field(init=False)
    url:str = field(init=False)

    # for petscan
    ps_params:tuple = field(init=False)

    # for interwikilinks
    interwiki_prefix:str = field(init=False)


    def __post_init__(self) -> None:
        if self.dbname in [ 'mediawikiwiki', 'sourceswiki', 'ruwikimedia', 'sewikimedia', 'incubatorwiki', 'wikimaniawiki', 'outreachwiki' ]:
            raise RuntimeWarning(f'Project {self.dbname} is being ignored')

        self._init_meta_params()
        self.ps_params = self._init_petscan_params()
        self.interwiki_prefix = self._init_interwiki_prefix()


    def _init_meta_params(self) -> None:
        query = """SELECT lang, family, url FROM wiki WHERE is_closed=0 AND has_wikidata=1 AND dbname=%(dbname)s LIMIT 1"""
        with Replica('meta.analytics.db.svc.wikimedia.cloud', 'meta_p') as (_, cur):
            cur.execute(query, {'dbname' : self.dbname })
            if cur.rowcount != 1:
                raise RuntimeError(f'Found {cur.rowcount} results for dbname {self.dbname}')
            result = cur.fetchall()

        self.lang = result[0].get('lang')  # TODO: what about nb -> no?
        self.family = result[0].get('family')
        self.url = result[0].get('url')


    def _init_petscan_params(self) -> tuple[str, str]:
        if self.family in [ 'wikipedia', 'wikibooks', 'wikiquote', 'wiktionary', 'wikinews', 'wikisource', 'wikiversity', 'wikivoyage' ]:
            return (self.lang, self.family)

        if self.dbname=='wikidatawiki':
            return ('wikidata', 'wikimedia')

        if self.dbname=='specieswiki':
            return ('species', 'wikimedia')

        if self.dbname=='commonswiki':
            return ('commons', 'wikimedia')

        if self.dbname=='metawiki':
            return ('meta', 'wikimedia')

        raise RuntimeError(f'No petscan parameters found for project {self.dbname}')


    def _init_interwiki_prefix(self) -> str:
        if self.family in [ 'wikipedia', 'wikibooks', 'wikiquote', 'wiktionary', 'wikinews', 'wikisource', 'wikiversity', 'wikivoyage' ]:
            return f':{INTERWIKI_MAP.get(self.family, "")}{self.lang}:'

        if self.dbname == 'wikidatawiki':
            return ''

        if self.dbname == 'specieswiki':
            return ':species:'

        if self.dbname == 'commonswiki':
            return ':c:'

        if self.dbname == 'metawiki':
            return ':m:'

        raise RuntimeError(f'No interwiki prefix found for project {self.dbname}')


class Replica:
    def __init__(self, host:str=WIKIDATA_REPLICA_HOST, dbname:str=WIKIDATA_REPLICA_DB) -> None:
        self.connection = mariadb.connect(
            host=host,
            database=dbname,
            default_file=DB_DEFAULT_FILE,
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def __enter__(self):
        return (self.connection, self.cursor)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.connection.close()


def query_wdqs(query:str) -> Generator[dict, None, None]:
    response = requests.post(
        url=WDQS_ENDPOINT,
        data={
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


def make_report(project:Project) -> str:
    text = ''

    for row in query_wdqs(SPARQL_QUERY.format(url=project.url)):
        qid = row.get('item', {}).get('value', '').replace(WD, '')
        page_title = row.get('lemma', {}).get('value', '')
        text += TABLE_ROW.format(
            qid=qid,
            interwiki_prefix=project.interwiki_prefix,
            page_title=page_title
        )

    return text


def make_overview() -> tuple[str, int, int]:
    with Replica() as (_, cur):
        cur.execute(QUERY_1)
        results = cur.fetchall()

    idx = 0
    maxvalue = 0
    text = ''

    for row in results:
        dbname = row.get('dbname')
        cnt = row.get('cnt')
        if dbname is None or cnt is None:
            continue

        print(dbname, cnt)
        try:
            project = Project(dbname)
        except (RuntimeError, RuntimeWarning) as exception:
            print(exception)
            continue

        idx += 1
        with Replica() as (_, cur):
            cur.execute(QUERY_2, { 'dbname' : dbname })

            for cnt_without in cur:
                cnt = cnt_without.get('cnt')
                if cnt is None:
                    continue

                if cnt > maxvalue:
                    maxvalue = cnt

                text += TABLE_ROW_OVERVIEW.format(
                    dbname=dbname,
                    lang=project.lang,
                    family=project.family,
                    url=project.url,
                    iw=project.interwiki_prefix,
                    ps_lang=project.ps_params[0],
                    ps_family=project.ps_params[1],
                    cnt_without=cnt,
                    idx=idx,
                    cnt=cnt
                )

    return text, idx, maxvalue


def main():
    for dbname in [ 'dewiki', 'enwiki', 'eowiki', 'etwiki', 'frwiki', 'jawiki', 'nlwiki', 'ptwiki', 'ruwiki', 'svwiki', 'huwiki', 'simplewiki' ]:
        project = Project(dbname)

        report = make_report(project)
        text = f'{HEADER.format(lang_code=project.lang, timestamp=time.strftime("%Y-%m-%d %H:%M (%Z)"))}{report}'

        page = pwb.Page(SITE, f'Wikidata:Database reports/without claims by site/{dbname}')
        page.text = text
        page.save(summary=EDIT_SUMMARY, minor=False)


    report, idx, max_value = make_overview()
    stat = f'{{{{DR otherreport|max={max_value}|reportlength={idx}}}}}\n'
    text = stat + HEADER_OVERVIEW.format(timestamp=time.strftime("%Y-%m-%d %H:%M (%Z)")) + report + FOOTER_OVERVIEW
    summary = f'Bot: Updating database report: reportlength: {idx}; max: {max_value}'

    page = pwb.Page(SITE, 'Wikidata:Database reports/without claims by site')
    page.text = text
    page.save(summary=summary, minor=False)


if __name__=='__main__':
    main()
