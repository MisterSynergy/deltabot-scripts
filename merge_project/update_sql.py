# -*- coding: UTF-8 -*-
#licensed under CC0

from os.path import expanduser
import re

import mariadb
import pywikibot as pwb


SITE = pwb.Site('wikidata', 'wikidata')
PAGE = 'User:Pasleim/projectmerge-input'


def main() -> None:
    cnx = mariadb.connect(host='tools.db.svc.wikimedia.cloud', database='s53100__merge_status', default_file=f'{expanduser("~")}/replica.my.cnf')
    cur = cnx.cursor(dictionary=True)

    page = pwb.Page(SITE, PAGE)
    content = page.get()
    content = content.replace('-','_')

    #find new entries
    lines = content.split('\n')
    for line in lines:
        if line=='':
            continue

        if line[0]=='#' or line[0]=='<':  # comment
            continue

        res = re.search('([a-z_]+)\s+([a-z_]+)', line)
        if not res:  # invalid entry
            continue

        wiki1 = res.group(1)
        wiki2 = res.group(2)

        query = 'SELECT id FROM merge_status WHERE wiki1=%(wiki1)s AND wiki2=%(wiki2)s'
        params = { 'wiki1' : wiki1, 'wiki2' : wiki2 }

        cur.execute(query, params)

        if cur.rowcount == 0:
            insert_query = 'INSERT INTO merge_status (wiki1, wiki2, update_requested) VALUES (%(wiki1)s, %(wiki2)s, NOW())'
            insert_params = { 'wiki1' : wiki1, 'wiki2' : wiki2 }
            cur.execute(insert_query, insert_params)
            cnx.commit()

    #find removed entries
    cur.execute('SELECT id, wiki1, wiki2 FROM merge_status')
    for row in cur.fetchall():
        if f'{row.get("wiki1")} {row.get("wiki2")}' not in content:
            delete_query = 'DELETE FROM merge_status WHERE id=%(identifier)s'
            delete_params = { 'identifier' : row.get('id') }
            cur.execute(delete_query, delete_params)
            cnx.commit()

    cur.close()
    cnx.close()


if __name__ == '__main__':
    main()
