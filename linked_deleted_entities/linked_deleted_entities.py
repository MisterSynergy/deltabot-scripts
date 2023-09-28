#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import mariadb
import pywikibot
import time
import requests
from os.path import expanduser


SITE = pywikibot.Site('wikidata','wikidata')

HEADER = """Update: <onlyinclude>{update_timestamp}</onlyinclude>
{{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"
|-
! Entity !! count !! deleted by
"""

FOOTER = """|}

[[Category:Database reports|Deleted Wikidata entities that are still linked]]"""

TABLE_ROW = """|-
| {{{{{pql}|{title}}}}} || [{{{{fullurl:Special:WhatLinksHere/{title}}}}} {cnt}] || [[User:{user}]]
"""


def make_report() -> str:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf',
    )
    cur = db.cursor(dictionary=True)

    query = """SELECT
  CONVERT(pl_title USING utf8) AS pl_title,
  COUNT(*) AS cnt
FROM
  pagelinks
    LEFT JOIN page ON pl_title=page_title AND pl_namespace=page_namespace
WHERE
  (pl_from_namespace=0 OR pl_from_namespace=120)
  AND (pl_namespace=0 OR pl_namespace=120)
  AND page_id IS NULL
GROUP BY
  pl_title
ORDER BY
  COUNT(*) DESC, pl_namespace, pl_title"""

    cur.execute(query)

    text = ''
    for row in cur.fetchall():
        title = row.get('pl_title')
        if title is None:
            continue

        response = requests.get(
            url='https://www.wikidata.org/w/api.php',
            params={
                'action' : 'query',
                'list' : 'logevents',
                'leprop' : 'user|type',
                'letitle' : title,
                'format' : 'json',
            }
        )
        data = response.json()
        user = 'unknown'

        for logevent in data.get('query', {}).get('logevents', []):
            if logevent['type']=='delete' and logevent['action']=='delete':
                user = logevent['user']
                break

        text += TABLE_ROW.format(pql=title[0], title=title, cnt=f'{row.get("cnt", 0):,}', user=user)

    cur.close()
    db.close()

    return text


def main() -> None:
    report = make_report()
    text = HEADER.format(update_timestamp=time.strftime('%Y-%m-%d %H:%M (%Z)')) + report + FOOTER

    page = pywikibot.Page(SITE, 'Wikidata:Database reports/Deleted Wikidata entities that are still linked')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
