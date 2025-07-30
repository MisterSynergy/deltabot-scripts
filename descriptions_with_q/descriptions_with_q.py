#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import mariadb
import time
import pywikibot
from os.path import expanduser

SITE = pywikibot.Site('wikidata', 'wikidata')

HEADER = """Update: <onlyinclude>{update_timestamp}</onlyinclude>.

{{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"
|-
! item !! language !! description
"""

TABLE_ROW = """|-
| [[Q{qid_numeric}]] || {language_code} || <nowiki>{description}</nowiki>
"""

FOOTER = """|}

[[Category:Database reports]]"""


def make_report() -> str:
    db = mariadb.connect(
        host='termstore.wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf',
    )
    cur = db.cursor(dictionary=True)

    query = """SELECT
  wbit_item_id AS id,
  CONVERT(wbxl_language USING utf8) AS language,
  CONVERT(wbx_text USING utf8) AS text
FROM
  wbt_item_terms
    LEFT JOIN wbt_term_in_lang ON wbit_term_in_lang_id=wbtl_id
    LEFT JOIN wbt_type ON wbtl_type_id=wby_id
    LEFT JOIN wbt_text_in_lang ON wbtl_text_in_lang_id=wbxl_id
    LEFT JOIN wbt_text ON wbxl_text_id=wbx_id
WHERE
  wby_name='description'
  AND wbx_text REGEXP 'Q[1-9][0-9]{3}'"""

    cur.execute(query)
    text = ''
    items = []
    for row in cur.fetchall():
        items.append([row.get('id', 0), row.get('language', ''), row.get('text', '')])

    items.sort(key=lambda x: x[0])

    for row in items:
        text += TABLE_ROW.format(qid_numeric=row[0], language_code=row[1], description=row[2])

    cur.close()
    db.close()

    return text


def main():
    report = make_report()
    text = HEADER.format(update_timestamp=time.strftime('%Y-%m-%d %H:%M (%Z)')) + report + FOOTER

    page = pywikibot.Page(SITE, 'Wikidata:Database reports/Descriptions with Q')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__ == "__main__":
    main()
