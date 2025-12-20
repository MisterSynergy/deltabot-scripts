#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import datetime
from pathlib import Path
import re
from time import strftime

import mariadb
import pywikibot as pwb


DBNAMES = [
    'dewiki',
    'fawiki',
    'frwiki',
    'nlwiki',
    'ptwiki',
    'ruwiki',
]

HEADER = """A list of {dbname} pages which were disconnected from Wikidata. Data as of <onlyinclude>{update_timestamp}</onlyinclude>.

{{| class="wikitable sortable" style="width:100%; margin:auto;"
|-
! Page !! Item !! Comment !! User !! Time
"""

TABLE_ROW = """|-
| [[:{iw_prefix}:{page_title}]] || [[{qid}]] || <nowiki>{comment}</nowiki> || [[User:{user_name}|{user_name}]] || {timestamp}
"""

FOOTER = """|}

[[Category:Database reports|removed sitelinks]]"""


def make_report(dbname:str) -> str:
    db = mariadb.connect(
        host=f'{dbname}.analytics.db.svc.wikimedia.cloud',
        database=f'{dbname}_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cur = db.cursor(dictionary=True)

    query = """SELECT
    CONVERT(page_title USING utf8) AS page_title,
    CONVERT(comment_text USING utf8) AS comment_text,
    CONVERT(actor_name USING utf8) AS actor_name,
    CONVERT(rc_timestamp USING utf8) AS rc_timestamp,
    CONVERT(rc_params USING utf8) AS rc_params
FROM
    page
        JOIN recentchanges ON rc_cur_id=page_id
            JOIN comment_recentchanges ON rc_comment_id=comment_id
            JOIN actor_recentchanges ON rc_actor=actor_id
        LEFT JOIN page_props ON page_id=pp_page AND pp_propname='wikibase_item'
WHERE
    rc_source='wb'
    AND page_namespace=0
    AND page_is_redirect=0
    AND pp_page IS NULL
ORDER BY
    page_title ASC"""

    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    db.close()

    text = ''
    for row in result:
        page_title = row.get('page_title')
        rc_comment = row.get('comment_text')
        rc_user_text = row.get('actor_name')
        rc_timestamp = row.get('rc_timestamp')
        rc_params = row.get('rc_params')

        if page_title is None or rc_comment is None or rc_user_text is None or rc_timestamp is None or rc_params is None:
            continue

        if dbname not in rc_params:
            continue

        timestamp = datetime.strptime(rc_timestamp, '%Y%m%d%H%M%S')

        res = re.search('"(Q\d+)"', rc_params)
        if res:
            qid = res.group(1)
        else:
            qid = ''

        text += TABLE_ROW.format(
            iw_prefix=dbname[:-4],
            page_title=page_title.replace('_', ' '),
            qid=qid,
            comment=rc_comment,
            user_name=rc_user_text.replace('wikidata>', ''),
            timestamp=timestamp.strftime('%Y-%m-%d %H:%M'),
        )


    return text


def main() -> None:
    for dbname in DBNAMES:
        text = HEADER.format(dbname=dbname, update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report(dbname) + FOOTER

        page = pwb.Page(pwb.Site('wikidata', 'wikidata'), f'Wikidata:Database reports/removed sitelinks/{dbname}')
        page.text = text
        page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
