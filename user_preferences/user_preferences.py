# !/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from os.path import expanduser
from time import strftime

import mariadb
import pywikibot


HEADER = 'Update: <onlyinclude>{update_timestamp}</onlyinclude>\n'
SUBHEADER_1 = '== Gender ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Gender !! Users\n'
SUBHEADER_2 = '== Language ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Language !! Users\n'
SUBHEADER_3 = '== Skin ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Skin !! Users\n'
SUBFOOTER = '|}\n\n'
FOOTER = '[[Category:Wikidata statistics]]'
TABLE_ROW = '|-\n| {preference} || {cnt}\n'


def make_report(db, query) -> str:
    cur = db.cursor(dictionary=True)
    cur.execute(query)

    text = ''
    for row in cur:
        preference = row.get('up_value')
        cnt = row.get('cnt')

        if preference is None or cnt is None:
            continue

        text += TABLE_ROW.format(preference=preference, cnt=cnt)

    cur.close()

    return text


def main() -> None:
    db = mariadb.connect(
        host='wikidatawiki.analytics.db.svc.wikimedia.cloud',
        database='wikidatawiki_p',
        default_file=f'{expanduser("~")}/replica.my.cnf',
    )

    query1 = 'SELECT CONVERT(up_value USING utf8) AS up_value, COUNT(*) AS cnt FROM user_properties WHERE up_property="gender" GROUP BY up_value'
    report1 = make_report(db, query1)

    query2 = 'SELECT CONVERT(up_value USING utf8) AS up_value, COUNT(*) AS cnt FROM user_properties_anon WHERE up_property="language" GROUP BY up_value'
    report2 = make_report(db, query2)

    query3 = 'SELECT CONVERT(up_value USING utf8) AS up_value, COUNT(*) AS cnt FROM user_properties_anon WHERE up_property="skin" GROUP BY up_value'
    report3 = make_report(db, query3)

    db.close()

    text = HEADER.format(update_timestamp=strftime('%Y-%m-%d %H:%M (%Z)')) + SUBHEADER_1 + report1 + \
        SUBFOOTER + SUBHEADER_2 + report2 + SUBFOOTER + \
        SUBHEADER_3 + report3 + SUBFOOTER + FOOTER

    page = pywikibot.Page(pywikibot.Site('wikidata', 'wikidata'), 'Wikidata:Database reports/User preferences')
    page.text = text
    page.save(summary='Bot:Updating database report', minor=False)


if __name__=='__main__':
    main()
