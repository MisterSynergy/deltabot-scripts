#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
from time import strftime

import mariadb
import pywikibot as pwb


HEADER = """Update: <onlyinclude>{update_timestamp}</onlyinclude>
==Items with the most links but without statements==
{{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"
|-
! Item !! # links
"""
MIDDLE = """|}

==Items with the most sitelinks but without statements==
{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"
|-
! Item !! # sitelinks
"""
FOOTER = """|}

[[Category:Database reports|Popular items without claims]]"""
TABLE_ROW = """|-
| {{{{Q|{qid}}}}} || {cnt}
"""

QUERY_1 = """SELECT
    CONVERT(pl_title USING utf8) AS qid,
    COUNT(*) AS cnt
FROM
    pagelinks
WHERE
    pl_from_namespace=0
    AND pl_namespace=0
    AND pl_title IN (
        SELECT
            page_title
        FROM
            page
                JOIN page_props ON page_id=pp_page
        WHERE
            pp_propname='wb-claims'
            AND pp_value=0
    )
GROUP BY
    pl_title
ORDER BY
    cnt DESC
LIMIT
    100"""

QUERY_2 = """SELECT
    CONVERT(page_title USING utf8) AS qid,
    CONVERT(ppsitelinks.pp_value USING utf8) AS cnt
FROM
    page_props AS ppclaims
        JOIN page ON ppclaims.pp_page=page_id AND page_namespace=0 AND page_is_redirect=0
        JOIN page_props AS ppsitelinks ON page_id=ppsitelinks.pp_page AND ppsitelinks.pp_propname='wb-sitelinks'
WHERE
    ppclaims.pp_propname='wb-claims'
    AND ppclaims.pp_value=0
ORDER BY
    CAST(ppsitelinks.pp_value AS int) DESC
LIMIT
    100"""


def make_report(db, query:str) -> str:
    cursor = db.cursor(dictionary=True)
    cursor.execute(query)

    text = ''
    for row in cursor:
        qid = row.get('qid')
        cnt = row.get('cnt')

        if qid is None or cnt is None:
            continue

        text += TABLE_ROW.format(qid=qid, cnt=cnt)

    cursor.close()

    return text


def main() -> None:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf',
    )

    report1 = make_report(db, QUERY_1)
    report2 = make_report(db, QUERY_2)

    db.close()

    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + report1 + MIDDLE + report2 + FOOTER
  
    page = pwb.Page(pwb.Site('wikidata', 'wikidata'), 'Wikidata:Database reports/Popular items without claims')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
