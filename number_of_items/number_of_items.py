#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser

import mariadb
import pywikibot as pwb


DB_DEFAULT_FILE = f'{expanduser("~")}/replica.my.cnf'
WIKIDATA_REPLICA_HOST = 'wikidatawiki.analytics.db.svc.wikimedia.cloud'
WIKIDATA_REPLICA_DB = 'wikidatawiki_p'

SITE = pwb.Site('wikidata', 'wikidata')
TEMPLATE_PAGE = 'Template:Numberofarticles'


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


def main() -> None:
    with Replica() as (_, cur):
        cur.execute('SELECT COUNT(*) as cnt FROM page WHERE page_namespace=0 AND page_is_redirect=0')
        result = cur.fetchall()

    page = pwb.Page(SITE, TEMPLATE_PAGE)
    page.text = str(result[0].get('cnt', 0))
    page.save(summary='upd', minor=False)


if __name__=='__main__':
    main()
