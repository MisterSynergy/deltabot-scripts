#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from pathlib import Path
from time import strftime

import mariadb
import pywikibot


HEADER_1 = '{{{{FULLPAGENAME}}/Header/{{#ifexist:{{FULLPAGENAME}}/Header/{{int:lang}}|{{int:lang}}|en}}}}\n'
HEADER_2 = 'Update: <onlyinclude>{update_timestamp}</onlyinclude>.\n\n{{| class="wikitable sortable plainlinks" style="width:100%; margin:auto;"\n|-\n! {{{{int:userlogin-yourname}}}} !! {{{{int:deletionlog}}}}\n'
TABLE_ROW = '|-\n| [[User:{username}|{username}]] || [{{{{fullurl:Special:Log/delete|user={username_underscore}}}}} {cnt}]\n'
FOOTER = '|}\n\n[[Category:Wikidata statistics]]\n[[Category:Wikidata administrators]]'


def make_report() -> str:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cursor = db.cursor(dictionary=True)

    query = """SELECT
    CONVERT(actor_name USING utf8) AS actor_name,
    COUNT(*) AS cnt
FROM
    logging
        JOIN actor ON log_actor=actor_id
WHERE
    log_action="delete"
    AND actor_user IN (
        SELECT
            ug_user
        FROM
            user_groups
        WHERE
            ug_group="sysop"
    )
GROUP BY
    log_actor
ORDER BY
    actor_name"""

    cursor.execute(query)
    text = ''
    for row in cursor:
        username = row.get('actor_name', '')
        text += TABLE_ROW.format(username=username, username_underscore=username.replace(' ', '_'), cnt=row.get('cnt', 0))

    return text


def main():
    text = HEADER_1 + HEADER_2.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report() + FOOTER

    page = pywikibot.Page(pywikibot.Site('wikidata', 'wikidata'), 'Wikidata:Database reports/Deletions')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
