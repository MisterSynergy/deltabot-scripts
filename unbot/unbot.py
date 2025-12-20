#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from datetime import date, timedelta
from pathlib import Path
from time import strftime

import mariadb
import pywikibot


HEADER = 'A list of active bots during the last month without bot flag. Update: <onlyinclude>{update_timestamp}</onlyinclude>\n\n{{| class="wikitable sortable" style="width:100%%; margin:auto;"\n|-\n! User !! Edits¹\n'
TABLE_ROW = '|-\n| {{{{User|{user_name}}}}} || {cnt}\n'
FOOTER = '|}\n\n¹edits in namespace 0 during the last 30 days\n[[Category:Database reports]]'

USER_NAME_WHITELIST = [
    'Paucabot',
    'Reubot',
]


def make_report() -> str:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=str(Path.home() / 'replica.my.cnf'),
    )
    cursor = db.cursor(dictionary=True)

    query = """SELECT
    CONVERT(actor_name USING utf8) AS user_name,
    COUNT(*) AS cnt
FROM
    recentchanges
        JOIN actor_recentchanges ON rc_actor=actor_id
WHERE
    rc_bot=0
    AND rc_namespace=0
    AND rc_timestamp>%(rc_timestamp)s
    AND (actor_name LIKE "%bot" OR actor_name LIKE "%Bot")
GROUP BY
    actor_name
HAVING
    actor_name NOT IN (
        SELECT
            user_name
        FROM
            user
                JOIN user_groups ON user_id=ug_user
        WHERE
            ug_group="bot"
    )"""

    params = { 'rc_timestamp' : (date.today()-timedelta(days=30)).strftime('%Y%m%d000000')}

    cursor.execute(query, params)
    text = ''
    for row in cursor:
        user_name = row.get('user_name')
        cnt = row.get('cnt')

        if user_name is None or cnt is None:
            continue

        if user_name in USER_NAME_WHITELIST:
            continue

        text += TABLE_ROW.format(user_name=user_name, cnt=cnt)

    return text


def main() -> None:
    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + make_report() + FOOTER

    page = pywikibot.Page(pywikibot.Site('wikidata','wikidata'), 'Wikidata:Database reports/Unauthorized bots')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
