# !/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import time

site = pywikibot.Site('wikidata', 'wikidata')

header = 'Update: <onlyinclude>{0}</onlyinclude>\n'

subheader1 = '== Gender ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Gender !! Users\n'
subheader2 = '== Language ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Language !! Users\n'
subheader3 = '== Skin ==\n{| class="wikitable sortable" style="width:40%;"\n|-\n! Skin !! Users\n'
subfooter = '|}\n\n'
footer = '[[Category:Wikidata statistics]]'

table_row = '|-\n| {0} || {1}\n'

query1 = 'SELECT up_value, count(*) FROM user_properties WHERE up_property="gender" GROUP BY up_value'
query2 = 'SELECT up_value, count(*) FROM user_properties_anon WHERE up_property="language" GROUP BY up_value'
query3 = 'SELECT up_value, count(*) FROM user_properties_anon WHERE up_property="skin" GROUP BY up_value'


def makeReport(db, query):
    cursor = db.cursor()
    cursor.execute(query)
    text = ''
    for val, cnt in cursor:
        text += table_row.format(val.decode(), ('{:,}'.format(cnt)))
    return text


def main():
    page = pywikibot.Page(site, 'Wikidata:Database reports/User preferences')
    db = MySQLdb.connect(host="wikidatawiki.analytics.db.svc.eqiad.wmflabs",
                         db="wikidatawiki_p", read_default_file="replica.my.cnf")
    report1 = makeReport(db, query1)
    report2 = makeReport(db, query2)
    report3 = makeReport(db, query3)
    text = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)")) + subheader1 + report1 + \
        subfooter + subheader2 + report2 + subfooter + \
        subheader3 + report3 + subfooter + footer
    page.put(text, summary='Bot:Updating database report', minorEdit=False)


if __name__ == "__main__":
    main()
